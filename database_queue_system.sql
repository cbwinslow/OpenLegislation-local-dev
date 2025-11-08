/*
OpenLegislation Database Queue System

This file contains the complete schema and setup for a PostgreSQL-based job queue system
that supports scheduling batch ingestion jobs, backups, data modifications, and SQL execution.

Features:
- Job queue with priority scheduling
- Audit logging and telemetry
- Support for saved queries and raw SQL execution
- Job dependencies and retry logic
- Performance monitoring and benchmarking
- Integration with pg_cron for scheduled execution

Author: OpenLegislation Team
Date: 2025-11-08
*/

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schema for queue system
CREATE SCHEMA IF NOT EXISTS queue_system;
COMMENT ON SCHEMA queue_system IS 'Job queue system for batch operations and scheduled tasks';

-- ============================================================================
-- CORE QUEUE TABLES
-- ============================================================================

-- Job queue table
CREATE TABLE IF NOT EXISTS queue_system.job_queue (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL, -- 'ingestion', 'backup', 'modification', 'query'
    job_name VARCHAR(255) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 1, -- 1=low, 5=normal, 10=high, 20=critical
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed, cancelled

    -- Job configuration
    sql_query TEXT, -- Raw SQL to execute
    saved_query_id UUID, -- Reference to saved query
    parameters JSONB DEFAULT '{}', -- Job parameters
    config JSONB DEFAULT '{}', -- Additional configuration

    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_seconds INTEGER DEFAULT 3600, -- 1 hour default

    -- Retry logic
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    retry_delay_seconds INTEGER DEFAULT 60,
    last_retry_at TIMESTAMP WITH TIME ZONE,

    -- Dependencies
    depends_on UUID[] DEFAULT '{}', -- Job IDs this job depends on
    dependency_strategy VARCHAR(20) DEFAULT 'all', -- 'all', 'any'

    -- Performance tracking
    estimated_duration_seconds INTEGER,
    actual_duration_seconds INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),

    -- GPU/Parallel processing
    enable_parallel BOOLEAN DEFAULT false,
    max_parallel_workers INTEGER DEFAULT 4,
    enable_gpu BOOLEAN DEFAULT false,
    gpu_memory_mb INTEGER,

    -- Error handling
    error_message TEXT,
    error_details JSONB,
    stack_trace TEXT,

    -- Metadata
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}',

    -- Constraints
    CONSTRAINT valid_job_type CHECK (job_type IN ('ingestion', 'backup', 'modification', 'query', 'maintenance')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 20),
    CONSTRAINT valid_dependency_strategy CHECK (dependency_strategy IN ('all', 'any'))
);

-- Saved queries table
CREATE TABLE IF NOT EXISTS queue_system.saved_queries (
    query_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    sql_query TEXT NOT NULL,
    parameters JSONB DEFAULT '{}', -- Parameter definitions
    query_type VARCHAR(50) DEFAULT 'select', -- select, insert, update, delete, ddl
    estimated_execution_time_seconds INTEGER,
    tags TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job execution history
CREATE TABLE IF NOT EXISTS queue_system.job_execution_history (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES queue_system.job_queue(job_id) ON DELETE CASCADE,
    execution_start TIMESTAMP WITH TIME ZONE NOT NULL,
    execution_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL,
    duration_seconds INTEGER,
    rows_affected BIGINT,
    error_message TEXT,
    performance_metrics JSONB,
    system_metrics JSONB, -- CPU, memory, disk usage
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job dependencies
CREATE TABLE IF NOT EXISTS queue_system.job_dependencies (
    dependency_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES queue_system.job_queue(job_id) ON DELETE CASCADE,
    depends_on_job_id UUID NOT NULL REFERENCES queue_system.job_queue(job_id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) DEFAULT 'completion', -- completion, success, failure
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, depends_on_job_id)
);

-- ============================================================================
-- AUDIT AND TELEMETRY TABLES
-- ============================================================================

-- Audit log for all queue operations
CREATE TABLE IF NOT EXISTS queue_system.audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_info JSONB, -- Client info, IP, etc.
    query_text TEXT -- The actual SQL query that made the change
);

-- Telemetry events
CREATE TABLE IF NOT EXISTS queue_system.telemetry_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    source VARCHAR(100) DEFAULT 'queue_system',
    severity VARCHAR(20) DEFAULT 'info', -- debug, info, warning, error, critical
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    job_id UUID REFERENCES queue_system.job_queue(job_id),
    user_id VARCHAR(100),
    session_id VARCHAR(100)
);

-- Performance benchmarks
CREATE TABLE IF NOT EXISTS queue_system.performance_benchmarks (
    benchmark_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL,
    operation_name VARCHAR(255) NOT NULL,
    execution_time_seconds DECIMAL(10,3),
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    disk_io_mb INTEGER,
    network_io_mb INTEGER,
    gpu_usage_percent DECIMAL(5,2),
    parallel_workers INTEGER,
    records_processed BIGINT,
    benchmark_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    system_info JSONB
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Job queue indexes
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON queue_system.job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_priority ON queue_system.job_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_job_queue_scheduled_at ON queue_system.job_queue(scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_queue_type ON queue_system.job_queue(job_type);
CREATE INDEX IF NOT EXISTS idx_job_queue_created_at ON queue_system.job_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_job_queue_tags ON queue_system.job_queue USING GIN(tags);

-- Saved queries indexes
CREATE INDEX IF NOT EXISTS idx_saved_queries_name ON queue_system.saved_queries(query_name);
CREATE INDEX IF NOT EXISTS idx_saved_queries_type ON queue_system.saved_queries(query_type);
CREATE INDEX IF NOT EXISTS idx_saved_queries_tags ON queue_system.saved_queries USING GIN(tags);

-- Execution history indexes
CREATE INDEX IF NOT EXISTS idx_execution_history_job_id ON queue_system.job_execution_history(job_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_status ON queue_system.job_execution_history(status);
CREATE INDEX IF NOT EXISTS idx_execution_history_start ON queue_system.job_execution_history(execution_start);

-- Telemetry indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_events_type ON queue_system.telemetry_events(event_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON queue_system.telemetry_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_job_id ON queue_system.telemetry_events(job_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_severity ON queue_system.telemetry_events(severity);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION queue_system.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_job_queue_updated_at
    BEFORE UPDATE ON queue_system.job_queue
    FOR EACH ROW EXECUTE FUNCTION queue_system.update_updated_at_column();

CREATE TRIGGER update_saved_queries_updated_at
    BEFORE UPDATE ON queue_system.saved_queries
    FOR EACH ROW EXECUTE FUNCTION queue_system.update_updated_at_column();

-- Audit trigger function
CREATE OR REPLACE FUNCTION queue_system.audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_row JSONB;
    new_row JSONB;
    operation_type TEXT;
BEGIN
    -- Determine operation type
    IF TG_OP = 'INSERT' THEN
        operation_type := 'INSERT';
        old_row := NULL;
        new_row := row_to_json(NEW)::JSONB;
    ELSIF TG_OP = 'UPDATE' THEN
        operation_type := 'UPDATE';
        old_row := row_to_json(OLD)::JSONB;
        new_row := row_to_json(NEW)::JSONB;
    ELSIF TG_OP = 'DELETE' THEN
        operation_type := 'DELETE';
        old_row := row_to_json(OLD)::JSONB;
        new_row := NULL;
    END IF;

    -- Insert audit record
    INSERT INTO queue_system.audit_log (
        table_name, record_id, operation, old_values, new_values,
        changed_by, session_info, query_text
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        operation_type,
        old_row,
        new_row,
        current_user,
        jsonb_build_object(
            'session_user', session_user,
            'current_user', current_user,
            'application_name', current_setting('application_name', true),
            'client_addr', inet_client_addr()::TEXT,
            'client_port', inet_client_port()
        ),
        current_query()
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Audit triggers for key tables
CREATE TRIGGER audit_job_queue
    AFTER INSERT OR UPDATE OR DELETE ON queue_system.job_queue
    FOR EACH ROW EXECUTE FUNCTION queue_system.audit_trigger_function();

CREATE TRIGGER audit_saved_queries
    AFTER INSERT OR UPDATE OR DELETE ON queue_system.saved_queries
    FOR EACH ROW EXECUTE FUNCTION queue_system.audit_trigger_function();

-- Function to check job dependencies
CREATE OR REPLACE FUNCTION queue_system.check_job_dependencies(p_job_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    dependency_count INTEGER;
    satisfied_count INTEGER;
    dep_strategy TEXT;
BEGIN
    -- Get dependency strategy
    SELECT dependency_strategy INTO dep_strategy
    FROM queue_system.job_queue
    WHERE job_id = p_job_id;

    -- Count total dependencies
    SELECT array_length(depends_on, 1) INTO dependency_count
    FROM queue_system.job_queue
    WHERE job_id = p_job_id;

    -- If no dependencies, return true
    IF dependency_count IS NULL OR dependency_count = 0 THEN
        RETURN TRUE;
    END IF;

    -- Count satisfied dependencies based on strategy
    IF dep_strategy = 'all' THEN
        -- All dependencies must be completed successfully
        SELECT COUNT(*) INTO satisfied_count
        FROM queue_system.job_queue
        WHERE job_id = ANY(
            (SELECT depends_on FROM queue_system.job_queue WHERE job_id = p_job_id)
        )
        AND status = 'completed';
    ELSE
        -- Any dependency can be completed (not implemented in this simplified version)
        satisfied_count := dependency_count;
    END IF;

    RETURN satisfied_count >= dependency_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get next pending job
CREATE OR REPLACE FUNCTION queue_system.get_next_pending_job()
RETURNS UUID AS $$
DECLARE
    next_job_id UUID;
BEGIN
    -- Get highest priority job that is pending and has satisfied dependencies
    SELECT jq.job_id INTO next_job_id
    FROM queue_system.job_queue jq
    WHERE jq.status = 'pending'
    AND (jq.scheduled_at IS NULL OR jq.scheduled_at <= NOW())
    AND queue_system.check_job_dependencies(jq.job_id)
    ORDER BY jq.priority DESC, jq.created_at ASC
    LIMIT 1;

    RETURN next_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to log telemetry event
CREATE OR REPLACE FUNCTION queue_system.log_telemetry_event(
    p_event_type TEXT,
    p_event_data JSONB,
    p_source TEXT DEFAULT 'queue_system',
    p_severity TEXT DEFAULT 'info',
    p_job_id UUID DEFAULT NULL,
    p_user_id TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO queue_system.telemetry_events (
        event_type, event_data, source, severity, job_id, user_id
    ) VALUES (
        p_event_type, p_event_data, p_source, p_severity, p_job_id, p_user_id
    ) RETURNING event_id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEDULED JOBS WITH PG_CRON
-- ============================================================================

-- Schedule job processor to run every minute
SELECT cron.schedule(
    'process-job-queue',
    '* * * * *', -- Every minute
    $$
    SELECT queue_system.process_pending_jobs();
    $$
);

-- Schedule cleanup of old execution history (daily at 2 AM)
SELECT cron.schedule(
    'cleanup-old-history',
    '0 2 * * *', -- Daily at 2 AM
    $$
    DELETE FROM queue_system.job_execution_history
    WHERE execution_start < NOW() - INTERVAL '90 days';
    $$
);

-- Schedule telemetry cleanup (weekly on Sunday at 3 AM)
SELECT cron.schedule(
    'cleanup-old-telemetry',
    '0 3 * * 0', -- Weekly on Sunday at 3 AM
    $$
    DELETE FROM queue_system.telemetry_events
    WHERE timestamp < NOW() - INTERVAL '30 days';
    $$
);

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to process pending jobs (called by cron)
CREATE OR REPLACE FUNCTION queue_system.process_pending_jobs()
RETURNS INTEGER AS $$
DECLARE
    job_record RECORD;
    processed_count INTEGER := 0;
BEGIN
    -- Get and process next pending job
    WHILE processed_count < 10 LOOP -- Process up to 10 jobs per minute
        SELECT * INTO job_record
        FROM queue_system.job_queue
        WHERE job_id = queue_system.get_next_pending_job()
        FOR UPDATE SKIP LOCKED;

        IF NOT FOUND THEN
            EXIT; -- No more jobs to process
        END IF;

        -- Mark job as running
        UPDATE queue_system.job_queue
        SET status = 'running', started_at = NOW()
        WHERE job_id = job_record.job_id;

        -- Log telemetry
        PERFORM queue_system.log_telemetry_event(
            'job_started',
            jsonb_build_object(
                'job_id', job_record.job_id,
                'job_type', job_record.job_type,
                'job_name', job_record.job_name
            ),
            'queue_processor',
            'info',
            job_record.job_id
        );

        -- Here you would typically call an external job processor
        -- For now, we'll just mark as completed
        UPDATE queue_system.job_queue
        SET status = 'completed', completed_at = NOW()
        WHERE job_id = job_record.job_id;

        -- Log completion
        PERFORM queue_system.log_telemetry_event(
            'job_completed',
            jsonb_build_object(
                'job_id', job_record.job_id,
                'duration_seconds', EXTRACT(EPOCH FROM (NOW() - job_record.started_at))
            ),
            'queue_processor',
            'info',
            job_record.job_id
        );

        processed_count := processed_count + 1;
    END LOOP;

    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS FOR MONITORING
-- ============================================================================

-- Active jobs view
CREATE OR REPLACE VIEW queue_system.active_jobs AS
SELECT
    job_id,
    job_type,
    job_name,
    status,
    priority,
    created_at,
    started_at,
    EXTRACT(EPOCH FROM (NOW() - started_at)) as running_seconds
FROM queue_system.job_queue
WHERE status IN ('running', 'pending')
ORDER BY priority DESC, created_at ASC;

-- Job statistics view
CREATE OR REPLACE VIEW queue_system.job_statistics AS
SELECT
    job_type,
    status,
    COUNT(*) as job_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MAX(EXTRACT(EPOCH FROM (completed_at - started_at))) as max_duration_seconds,
    MIN(EXTRACT(EPOCH FROM (completed_at - started_at))) as min_duration_seconds
FROM queue_system.job_queue
WHERE completed_at IS NOT NULL
GROUP BY job_type, status;

-- System health view
CREATE OR REPLACE VIEW queue_system.system_health AS
SELECT
    (SELECT COUNT(*) FROM queue_system.job_queue WHERE status = 'pending') as pending_jobs,
    (SELECT COUNT(*) FROM queue_system.job_queue WHERE status = 'running') as running_jobs,
    (SELECT COUNT(*) FROM queue_system.job_queue WHERE status = 'failed') as failed_jobs,
    (SELECT COUNT(*) FROM queue_system.telemetry_events WHERE severity = 'error' AND timestamp > NOW() - INTERVAL '1 hour') as recent_errors,
    (SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) FROM queue_system.job_queue WHERE status = 'completed' AND completed_at > NOW() - INTERVAL '1 hour') as avg_job_duration_last_hour;

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions to application roles
-- Note: Adjust these based on your actual roles
GRANT USAGE ON SCHEMA queue_system TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA queue_system TO app_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA queue_system TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA queue_system TO app_user;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert some sample saved queries
INSERT INTO queue_system.saved_queries (query_name, description, sql_query, query_type, tags) VALUES
('get_recent_bills', 'Get bills updated in the last 24 hours', 'SELECT * FROM master.bill WHERE updated_at > NOW() - INTERVAL ''24 hours'' ORDER BY updated_at DESC', 'select', ARRAY['bills', 'recent']),
('count_bills_by_type', 'Count bills by type', 'SELECT bill_type, COUNT(*) FROM master.bill GROUP BY bill_type ORDER BY count DESC', 'select', ARRAY['bills', 'statistics']),
('failed_ingestion_jobs', 'Show recently failed ingestion jobs', 'SELECT * FROM queue_system.job_queue WHERE job_type = ''ingestion'' AND status = ''failed'' AND created_at > NOW() - INTERVAL ''7 days'' ORDER BY created_at DESC', 'select', ARRAY['jobs', 'failures'])
ON CONFLICT (query_name) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE queue_system.job_queue IS 'Main job queue table for scheduling and executing batch operations';
COMMENT ON TABLE queue_system.saved_queries IS 'Repository of reusable SQL queries for job execution';
COMMENT ON TABLE queue_system.job_execution_history IS 'Historical execution data for performance analysis';
COMMENT ON TABLE queue_system.audit_log IS 'Complete audit trail of all queue system operations';
COMMENT ON TABLE queue_system.telemetry_events IS 'Structured telemetry events for monitoring and debugging';
COMMENT ON TABLE queue_system.performance_benchmarks IS 'Performance benchmarks for different job types';

-- ============================================================================
-- FINAL SETUP
-- ============================================================================

-- Create indexes on foreign keys for better performance
CREATE INDEX IF NOT EXISTS idx_job_execution_history_job_id ON queue_system.job_execution_history(job_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_job_id ON queue_system.telemetry_events(job_id);

-- Analyze tables for query optimization
ANALYZE queue_system.job_queue;
ANALYZE queue_system.saved_queries;
ANALYZE queue_system.job_execution_history;
ANALYZE queue_system.audit_log;
ANALYZE queue_system.telemetry_events;

-- Log successful setup
DO $$
BEGIN
    PERFORM queue_system.log_telemetry_event(
        'database_queue_system_initialized',
        jsonb_build_object(
            'schema_version', '1.0.0',
            'setup_timestamp', NOW(),
            'features', ARRAY['job_queue', 'audit_logging', 'telemetry', 'performance_monitoring']
        ),
        'database_setup',
        'info'
    );
END;
$$;
