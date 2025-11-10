/*
Enhanced Telemetry, Benchmarking, and Audit System for OpenLegislation

This schema provides comprehensive tracking of:
- AI agent thoughts, conversations, and communications
- SQL query results and performance metrics
- User interactions and system events
- File/folder health monitoring
- Benchmarking results
- Complete audit trails

Author: OpenLegislation Team
Date: 2025-11-08
*/

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schema for enhanced telemetry
CREATE SCHEMA IF NOT EXISTS telemetry_audit;
COMMENT ON SCHEMA telemetry_audit IS 'Enhanced telemetry, benchmarking, and audit logging system';

-- ============================================================================
-- AI AGENT COMMUNICATION AND THOUGHT TRACKING
-- ============================================================================

-- AI Agent registry
CREATE TABLE IF NOT EXISTS telemetry_audit.ai_agents (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(255) NOT NULL UNIQUE,
    agent_type VARCHAR(100) NOT NULL, -- 'ingestion', 'monitoring', 'benchmarking', 'health', 'telemetry'
    description TEXT,
    capabilities JSONB DEFAULT '{}', -- What the agent can do
    configuration JSONB DEFAULT '{}', -- Agent-specific settings
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE
);

-- AI Agent thoughts and reasoning
CREATE TABLE IF NOT EXISTS telemetry_audit.agent_thoughts (
    thought_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES telemetry_audit.ai_agents(agent_id) ON DELETE CASCADE,
    session_id VARCHAR(255), -- Session/context identifier
    thought_type VARCHAR(50) DEFAULT 'reasoning', -- 'reasoning', 'decision', 'observation', 'planning'
    thought_content TEXT NOT NULL,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    context_data JSONB DEFAULT '{}', -- Additional context
    thought_metadata JSONB DEFAULT '{}', -- Metadata about the thought process
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Agent conversations and communications
CREATE TABLE IF NOT EXISTS telemetry_audit.agent_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    from_agent_id UUID REFERENCES telemetry_audit.ai_agents(agent_id),
    to_agent_id UUID REFERENCES telemetry_audit.ai_agents(agent_id),
    from_user BOOLEAN DEFAULT false, -- True if message is from human user
    message_type VARCHAR(50) DEFAULT 'text', -- 'text', 'command', 'result', 'error'
    message_content TEXT NOT NULL,
    message_metadata JSONB DEFAULT '{}', -- Additional message data
    response_to UUID REFERENCES telemetry_audit.agent_conversations(conversation_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User interactions with AI agents
CREATE TABLE IF NOT EXISTS telemetry_audit.user_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255), -- User identifier (could be session ID, username, etc.)
    session_id VARCHAR(255) NOT NULL,
    agent_id UUID REFERENCES telemetry_audit.ai_agents(agent_id),
    interaction_type VARCHAR(50) NOT NULL, -- 'query', 'command', 'feedback', 'correction'
    user_input TEXT NOT NULL,
    agent_response TEXT,
    interaction_metadata JSONB DEFAULT '{}', -- Additional context
    user_satisfaction_rating INTEGER CHECK (user_satisfaction_rating BETWEEN 1 AND 5),
    response_time_seconds DECIMAL(10,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SQL QUERY TRACKING AND PERFORMANCE
-- ============================================================================

-- SQL Query execution tracking
CREATE TABLE IF NOT EXISTS telemetry_audit.sql_queries (
    query_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash VARCHAR(64) UNIQUE, -- For deduplication
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) DEFAULT 'select', -- 'select', 'insert', 'update', 'delete', 'ddl'
    parameters JSONB DEFAULT '{}', -- Query parameters used
    execution_context JSONB DEFAULT '{}', -- Where/why the query was executed

    -- Performance metrics
    execution_time_ms INTEGER,
    rows_affected BIGINT,
    result_size_bytes BIGINT,

    -- System metrics during execution
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    disk_io_mb DECIMAL(10,2),
    network_io_mb DECIMAL(10,2),

    -- Result summary (for SELECT queries)
    result_summary JSONB DEFAULT '{}',

    -- Error tracking
    error_message TEXT,
    error_code VARCHAR(50),

    -- Metadata
    executed_by VARCHAR(255), -- Agent name, user ID, or system component
    connection_info JSONB DEFAULT '{}', -- Database connection details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query performance benchmarks
CREATE TABLE IF NOT EXISTS telemetry_audit.query_benchmarks (
    benchmark_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID REFERENCES telemetry_audit.sql_queries(query_id),
    benchmark_name VARCHAR(255) NOT NULL,
    benchmark_category VARCHAR(100) DEFAULT 'performance', -- 'performance', 'accuracy', 'scalability'

    -- Benchmark metrics
    execution_time_ms INTEGER NOT NULL,
    throughput_qps DECIMAL(10,2), -- Queries per second
    latency_p50_ms INTEGER,
    latency_p95_ms INTEGER,
    latency_p99_ms INTEGER,

    -- Resource usage
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    peak_memory_usage_mb INTEGER,

    -- Test conditions
    concurrent_users INTEGER DEFAULT 1,
    data_volume_records BIGINT,
    test_duration_seconds INTEGER,

    -- Results and analysis
    benchmark_result JSONB DEFAULT '{}',
    recommendations TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- FILE AND SYSTEM HEALTH MONITORING
-- ============================================================================

-- File system health scans
CREATE TABLE IF NOT EXISTS telemetry_audit.file_health_scans (
    scan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_type VARCHAR(50) DEFAULT 'comprehensive', -- 'comprehensive', 'quick', 'targeted'
    scan_target VARCHAR(500), -- File path or directory scanned
    initiated_by VARCHAR(255), -- Agent or user who initiated

    -- Scan results
    total_files_scanned INTEGER DEFAULT 0,
    total_directories_scanned INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,

    -- Health metrics
    healthy_files INTEGER DEFAULT 0,
    corrupted_files INTEGER DEFAULT 0,
    missing_files INTEGER DEFAULT 0,
    oversized_files INTEGER DEFAULT 0,

    -- Issues found
    issues_found JSONB DEFAULT '[]', -- Array of issues with details
    critical_issues INTEGER DEFAULT 0,
    warning_issues INTEGER DEFAULT 0,

    -- Performance
    scan_duration_seconds DECIMAL(10,3),
    scan_metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual file health records
CREATE TABLE IF NOT EXISTS telemetry_audit.file_health_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES telemetry_audit.file_health_scans(scan_id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50),

    -- File attributes
    file_size_bytes BIGINT,
    modified_at TIMESTAMP WITH TIME ZONE,
    permissions VARCHAR(10),
    owner VARCHAR(255),

    -- Health status
    health_status VARCHAR(20) DEFAULT 'healthy', -- 'healthy', 'warning', 'critical', 'corrupted'
    health_score INTEGER CHECK (health_score BETWEEN 0 AND 100),

    -- Issues detected
    issues JSONB DEFAULT '[]',

    -- Content analysis (for code files)
    lines_of_code INTEGER,
    complexity_score DECIMAL(5,2),
    test_coverage_percent DECIMAL(5,2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Software dependency health
CREATE TABLE IF NOT EXISTS telemetry_audit.software_health (
    health_check_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component_name VARCHAR(255) NOT NULL,
    component_type VARCHAR(50) DEFAULT 'library', -- 'library', 'framework', 'tool', 'service'

    -- Version information
    current_version VARCHAR(50),
    latest_version VARCHAR(50),
    version_status VARCHAR(20) DEFAULT 'current', -- 'current', 'outdated', 'vulnerable'

    -- Health metrics
    health_status VARCHAR(20) DEFAULT 'healthy', -- 'healthy', 'warning', 'critical'
    health_score INTEGER CHECK (health_score BETWEEN 0 AND 100),

    -- Security information
    security_vulnerabilities INTEGER DEFAULT 0,
    critical_vulnerabilities INTEGER DEFAULT 0,

    -- Compatibility
    compatibility_issues JSONB DEFAULT '[]',

    -- Recommendations
    upgrade_recommended BOOLEAN DEFAULT false,
    upgrade_priority VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'

    last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- BENCHMARKING SYSTEM
-- ============================================================================

-- Benchmark test definitions
CREATE TABLE IF NOT EXISTS telemetry_audit.benchmark_definitions (
    benchmark_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    benchmark_name VARCHAR(255) NOT NULL UNIQUE,
    benchmark_category VARCHAR(100) NOT NULL, -- 'performance', 'accuracy', 'scalability', 'reliability'
    description TEXT,

    -- Test configuration
    test_type VARCHAR(50) NOT NULL, -- 'ingestion', 'query', 'processing', 'system'
    test_parameters JSONB DEFAULT '{}',
    expected_duration_seconds INTEGER,
    resource_requirements JSONB DEFAULT '{}',

    -- Success criteria
    success_criteria JSONB DEFAULT '{}',

    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Benchmark execution results
CREATE TABLE IF NOT EXISTS telemetry_audit.benchmark_results (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    benchmark_id UUID NOT NULL REFERENCES telemetry_audit.benchmark_definitions(benchmark_id),
    execution_id VARCHAR(255) NOT NULL, -- Unique execution identifier

    -- Execution details
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,3),

    -- Results
    success BOOLEAN DEFAULT false,
    result_score DECIMAL(8,4), -- Overall score (0.0000 to 100.0000)
    result_metrics JSONB DEFAULT '{}',

    -- Performance metrics
    cpu_usage_avg DECIMAL(5,2),
    cpu_usage_peak DECIMAL(5,2),
    memory_usage_avg_mb INTEGER,
    memory_usage_peak_mb INTEGER,
    disk_io_total_mb DECIMAL(10,2),
    network_io_total_mb DECIMAL(10,2),

    -- GPU metrics (if applicable)
    gpu_usage_avg DECIMAL(5,2),
    gpu_memory_usage_avg_mb INTEGER,

    -- Detailed results
    detailed_results JSONB DEFAULT '{}',
    error_messages JSONB DEFAULT '[]',

    -- Analysis
    performance_analysis TEXT,
    recommendations TEXT,

    executed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ENHANCED TELEMETRY EVENTS
-- ============================================================================

-- Comprehensive telemetry events
CREATE TABLE IF NOT EXISTS telemetry_audit.telemetry_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) DEFAULT 'system', -- 'system', 'user', 'agent', 'performance', 'security'

    -- Event data
    event_data JSONB NOT NULL,
    event_metadata JSONB DEFAULT '{}',

    -- Context
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    agent_id UUID REFERENCES telemetry_audit.ai_agents(agent_id),
    component_name VARCHAR(255), -- Which system component generated the event

    -- Severity and impact
    severity VARCHAR(20) DEFAULT 'info', -- 'debug', 'info', 'warning', 'error', 'critical'
    impact_level VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'

    -- Performance context
    performance_context JSONB DEFAULT '{}', -- CPU, memory, etc. at time of event

    -- Location/context information
    file_path VARCHAR(1000),
    function_name VARCHAR(255),
    line_number INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- AUDIT LOGS WITH COMPREHENSIVE TRACKING
-- ============================================================================

-- Comprehensive audit log
CREATE TABLE IF NOT EXISTS telemetry_audit.audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_type VARCHAR(50) NOT NULL, -- 'access', 'modification', 'execution', 'communication'

    -- What happened
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL, -- 'file', 'database', 'agent', 'user', 'system'
    resource_id VARCHAR(255), -- ID or path of the resource
    resource_name VARCHAR(255),

    -- Who did it
    actor_type VARCHAR(20) DEFAULT 'system', -- 'user', 'agent', 'system', 'external'
    actor_id VARCHAR(255),
    actor_name VARCHAR(255),

    -- Context
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,

    -- Before/after states
    old_values JSONB,
    new_values JSONB,
    changes_summary TEXT,

    -- Additional context
    audit_metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',

    -- Security and compliance
    confidentiality_level VARCHAR(20) DEFAULT 'internal', -- 'public', 'internal', 'confidential', 'restricted'
    compliance_flags TEXT[] DEFAULT '{}', -- GDPR, HIPAA, etc.

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- AI Agents indexes
CREATE INDEX IF NOT EXISTS idx_ai_agents_type ON telemetry_audit.ai_agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_ai_agents_active ON telemetry_audit.ai_agents(is_active) WHERE is_active = true;

-- Agent thoughts indexes
CREATE INDEX IF NOT EXISTS idx_agent_thoughts_agent ON telemetry_audit.agent_thoughts(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_thoughts_session ON telemetry_audit.agent_thoughts(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_thoughts_type ON telemetry_audit.agent_thoughts(thought_type);
CREATE INDEX IF NOT EXISTS idx_agent_thoughts_created ON telemetry_audit.agent_thoughts(created_at);

-- Conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_session ON telemetry_audit.agent_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_from_agent ON telemetry_audit.agent_conversations(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_to_agent ON telemetry_audit.agent_conversations(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON telemetry_audit.agent_conversations(created_at);

-- User interactions indexes
CREATE INDEX IF NOT EXISTS idx_user_interactions_user ON telemetry_audit.user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_session ON telemetry_audit.user_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_agent ON telemetry_audit.user_interactions(agent_id);

-- SQL queries indexes
CREATE INDEX IF NOT EXISTS idx_sql_queries_hash ON telemetry_audit.sql_queries(query_hash);
CREATE INDEX IF NOT EXISTS idx_sql_queries_type ON telemetry_audit.sql_queries(query_type);
CREATE INDEX IF NOT EXISTS idx_sql_queries_executed_by ON telemetry_audit.sql_queries(executed_by);
CREATE INDEX IF NOT EXISTS idx_sql_queries_created ON telemetry_audit.sql_queries(created_at);

-- Telemetry events indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_events_type ON telemetry_audit.telemetry_events(event_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_category ON telemetry_audit.telemetry_events(event_category);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_severity ON telemetry_audit.telemetry_events(severity);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_created ON telemetry_audit.telemetry_events(created_at);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_agent ON telemetry_audit.telemetry_events(agent_id);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_type ON telemetry_audit.audit_log(audit_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON telemetry_audit.audit_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON telemetry_audit.audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON telemetry_audit.audit_log(created_at);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION telemetry_audit.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_benchmark_definitions_updated_at
    BEFORE UPDATE ON telemetry_audit.benchmark_definitions
    FOR EACH ROW EXECUTE FUNCTION telemetry_audit.update_updated_at_column();

-- Function to log telemetry event
CREATE OR REPLACE FUNCTION telemetry_audit.log_telemetry_event(
    p_event_type TEXT,
    p_event_data JSONB,
    p_event_category TEXT DEFAULT 'system',
    p_severity TEXT DEFAULT 'info',
    p_session_id TEXT DEFAULT NULL,
    p_user_id TEXT DEFAULT NULL,
    p_agent_id UUID DEFAULT NULL,
    p_component_name TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO telemetry_audit.telemetry_events (
        event_type, event_category, event_data, session_id, user_id,
        agent_id, component_name, severity
    ) VALUES (
        p_event_type, p_event_category, p_event_data, p_session_id, p_user_id,
        p_agent_id, p_component_name, p_severity
    ) RETURNING event_id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

-- Function to log audit event
CREATE OR REPLACE FUNCTION telemetry_audit.log_audit_event(
    p_audit_type TEXT,
    p_action TEXT,
    p_resource_type TEXT,
    p_resource_id TEXT DEFAULT NULL,
    p_resource_name TEXT DEFAULT NULL,
    p_actor_type TEXT DEFAULT 'system',
    p_actor_id TEXT DEFAULT NULL,
    p_actor_name TEXT DEFAULT NULL,
    p_session_id TEXT DEFAULT NULL,
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_changes_summary TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    audit_id UUID;
BEGIN
    INSERT INTO telemetry_audit.audit_log (
        audit_type, action, resource_type, resource_id, resource_name,
        actor_type, actor_id, actor_name, session_id,
        old_values, new_values, changes_summary
    ) VALUES (
        p_audit_type, p_action, p_resource_type, p_resource_id, p_resource_name,
        p_actor_type, p_actor_id, p_actor_name, p_session_id,
        p_old_values, p_new_values, p_changes_summary
    ) RETURNING audit_id INTO audit_id;

    RETURN audit_id;
END;
$$ LANGUAGE plpgsql;

-- Function to record agent thought
CREATE OR REPLACE FUNCTION telemetry_audit.record_agent_thought(
    p_agent_id UUID,
    p_session_id TEXT,
    p_thought_type TEXT,
    p_thought_content TEXT,
    p_confidence_score DECIMAL DEFAULT NULL,
    p_context_data JSONB DEFAULT '{}',
    p_thought_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    thought_id UUID;
BEGIN
    INSERT INTO telemetry_audit.agent_thoughts (
        agent_id, session_id, thought_type, thought_content,
        confidence_score, context_data, thought_metadata
    ) VALUES (
        p_agent_id, p_session_id, p_thought_type, p_thought_content,
        p_confidence_score, p_context_data, p_thought_metadata
    ) RETURNING thought_id INTO thought_id;

    -- Update agent's last active timestamp
    UPDATE telemetry_audit.ai_agents
    SET last_active_at = NOW()
    WHERE agent_id = p_agent_id;

    RETURN thought_id;
END;
$$ LANGUAGE plpgsql;

-- Function to record agent conversation
CREATE OR REPLACE FUNCTION telemetry_audit.record_agent_conversation(
    p_session_id TEXT,
    p_from_agent_id UUID DEFAULT NULL,
    p_to_agent_id UUID DEFAULT NULL,
    p_from_user BOOLEAN DEFAULT false,
    p_message_type TEXT DEFAULT 'text',
    p_message_content TEXT,
    p_message_metadata JSONB DEFAULT '{}',
    p_response_to UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    conversation_id UUID;
BEGIN
    INSERT INTO telemetry_audit.agent_conversations (
        session_id, from_agent_id, to_agent_id, from_user,
        message_type, message_content, message_metadata, response_to
    ) VALUES (
        p_session_id, p_from_agent_id, p_to_agent_id, p_from_user,
        p_message_type, p_message_content, p_message_metadata, p_response_to
    ) RETURNING conversation_id INTO conversation_id;

    RETURN conversation_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEDULED MAINTENANCE WITH PG_CRON
-- ============================================================================

-- Clean up old telemetry events (daily at 1 AM)
SELECT cron.schedule(
    'cleanup-old-telemetry-events',
    '0 1 * * *', -- Daily at 1 AM
    $$
    DELETE FROM telemetry_audit.telemetry_events
    WHERE created_at < NOW() - INTERVAL '90 days';
    $$
);

-- Clean up old agent thoughts (weekly on Sunday at 2 AM)
SELECT cron.schedule(
    'cleanup-old-agent-thoughts',
    '0 2 * * 0', -- Weekly on Sunday at 2 AM
    $$
    DELETE FROM telemetry_audit.agent_thoughts
    WHERE created_at < NOW() - INTERVAL '30 days';
    $$
);

-- Clean up old conversations (daily at 3 AM)
SELECT cron.schedule(
    'cleanup-old-conversations',
    '0 3 * * *', -- Daily at 3 AM
    $$
    DELETE FROM telemetry_audit.agent_conversations
    WHERE created_at < NOW() - INTERVAL '60 days';
    $$
);

-- ============================================================================
-- MONITORING VIEWS
-- ============================================================================

-- System health overview
CREATE OR REPLACE VIEW telemetry_audit.system_health_overview AS
SELECT
    (SELECT COUNT(*) FROM telemetry_audit.ai_agents WHERE is_active = true) as active_agents,
    (SELECT COUNT(*) FROM telemetry_audit.telemetry_events WHERE severity = 'error' AND created_at > NOW() - INTERVAL '1 hour') as recent_errors,
    (SELECT COUNT(*) FROM telemetry_audit.telemetry_events WHERE severity = 'warning' AND created_at > NOW() - INTERVAL '1 hour') as recent_warnings,
    (SELECT COUNT(*) FROM telemetry_audit.agent_conversations WHERE created_at > NOW() - INTERVAL '1 hour') as recent_conversations,
    (SELECT COUNT(*) FROM telemetry_audit.sql_queries WHERE created_at > NOW() - INTERVAL '1 hour') as recent_queries,
    (SELECT AVG(execution_time_ms) FROM telemetry_audit.sql_queries WHERE created_at > NOW() - INTERVAL '1 hour' AND execution_time_ms IS NOT NULL) as avg_query_time_ms
;

-- Agent activity summary
CREATE OR REPLACE VIEW telemetry_audit.agent_activity_summary AS
SELECT
    a.agent_name,
    a.agent_type,
    COUNT(t.thought_id) as total_thoughts,
    COUNT(c.conversation_id) as total_conversations,
    MAX(a.last_active_at) as last_active_at,
    AVG(t.confidence_score) as avg_confidence_score
FROM telemetry_audit.ai_agents a
LEFT JOIN telemetry_audit.agent_thoughts t ON a.agent_id = t.agent_id
LEFT JOIN telemetry_audit.agent_conversations c ON a.agent_id = c.from_agent_id
WHERE a.is_active = true
GROUP BY a.agent_id, a.agent_name, a.agent_type
ORDER BY total_thoughts DESC;

-- Performance metrics summary
CREATE OR REPLACE VIEW telemetry_audit.performance_metrics_summary AS
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as total_queries,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms,
    AVG(cpu_usage_percent) as avg_cpu_usage,
    AVG(memory_usage_mb) as avg_memory_usage_mb
FROM telemetry_audit.sql_queries
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant permissions to application roles
GRANT USAGE ON SCHEMA telemetry_audit TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA telemetry_audit TO app_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA telemetry_audit TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA telemetry_audit TO app_user;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Register initial AI agents
INSERT INTO telemetry_audit.ai_agents (agent_name, agent_type, description, capabilities) VALUES
('DataIngestionAgent', 'ingestion', 'Handles data ingestion operations with GPU acceleration', '["data_ingestion", "gpu_processing", "parallel_processing", "api_integration"]'),
('MonitoringAgent', 'monitoring', 'Real-time system monitoring and alerting', '["system_monitoring", "performance_tracking", "alert_generation", "health_checks"]'),
('BenchmarkingAgent', 'benchmarking', 'Performance benchmarking and optimization', '["performance_testing", "benchmark_execution", "optimization_recommendations", "scalability_analysis"]'),
('TelemetryAgent', 'telemetry', 'Telemetry collection and analysis', '["event_collection", "metrics_aggregation", "trend_analysis", "reporting"]'),
('HealthScanAgent', 'health', 'File and software health scanning', '["file_analysis", "dependency_checking", "security_scanning", "integrity_verification"]'),
('AuditAgent', 'audit', 'Audit logging and compliance monitoring', '["audit_logging", "compliance_checking", "anomaly_detection", "forensic_analysis"]'),
('ConfigAgent', 'configuration', 'Configuration management and optimization', '["config_management", "parameter_tuning", "environment_setup", "deployment_optimization"]')
ON CONFLICT (agent_name) DO NOTHING;

-- Create sample benchmark definitions
INSERT INTO telemetry_audit.benchmark_definitions (
    benchmark_name, benchmark_category, description, test_type, test_parameters,
    expected_duration_seconds, success_criteria
) VALUES
('Congress API Ingestion Benchmark', 'performance', 'Benchmark congress.gov API data ingestion performance', 'ingestion',
 '{"congress_range": [110, 118], "api_key_required": false}',
 300, '{"max_duration_seconds": 600, "min_records_per_second": 10}'),

('SQL Query Performance Benchmark', 'performance', 'Benchmark complex SQL query performance', 'query',
 '{"query_complexity": "high", "data_volume": "large"}',
 60, '{"max_execution_time_ms": 5000, "max_memory_mb": 1024}'),

('File System Health Scan Benchmark', 'reliability', 'Benchmark file system health scanning', 'system',
 '{"scan_depth": "full", "parallel_workers": 4}',
 180, '{"max_scan_time_seconds": 300, "min_files_per_second": 1000}'),

('GPU Processing Benchmark', 'performance', 'Benchmark GPU-accelerated data processing', 'processing',
 '{"data_size_gb": 1, "processing_type": "dataframe_operations"}',
 120, '{"gpu_utilization_percent": 80, "speedup_factor": 5}')
ON CONFLICT (benchmark_name) DO NOTHING;

-- ============================================================================
-- FINAL SETUP
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE telemetry_audit.ai_agents;
ANALYZE telemetry_audit.agent_thoughts;
ANALYZE telemetry_audit.agent_conversations;
ANALYZE telemetry_audit.telemetry_events;
ANALYZE telemetry_audit.audit_log;
ANALYZE telemetry_audit.sql_queries;

-- Log successful setup
DO $$
BEGIN
    PERFORM telemetry_audit.log_telemetry_event(
        'enhanced_telemetry_audit_system_initialized',
        jsonb_build_object(
            'schema_version', '1.0.0',
            'setup_timestamp', NOW(),
            'features', ARRAY['ai_agent_tracking', 'telemetry_system', 'audit_logging', 'benchmarking', 'health_monitoring'],
            'agents_registered', (SELECT COUNT(*) FROM telemetry_audit.ai_agents),
            'benchmarks_defined', (SELECT COUNT(*) FROM telemetry_audit.benchmark_definitions)
        ),
        'database_setup',
        'info'
    );
END;
$$;
