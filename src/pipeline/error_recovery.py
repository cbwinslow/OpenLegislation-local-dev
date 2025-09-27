"""
Enhanced Error Handling and Recovery Pipeline

This module provides comprehensive error handling, intelligent retry mechanisms,
circuit breaker patterns, and dead letter queue management for enterprise-grade
resilience and fault tolerance.
"""

import time
import asyncio
import random
from typing import Dict, List, Optional, Any, Callable, Union, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import traceback
import json

from models.vector_document import VectorDocument, ProcessingStatus
from src.audit.audit_manager import get_audit_manager, AuditContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ErrorCategory(str, Enum):
    """Categories of errors"""
    NETWORK = "NETWORK"
    DATABASE = "DATABASE"
    VALIDATION = "VALIDATION"
    PROCESSING = "PROCESSING"
    EXTERNAL_API = "EXTERNAL_API"
    SYSTEM = "SYSTEM"
    COMPLIANCE = "COMPLIANCE"

class RecoveryStrategy(str, Enum):
    """Recovery strategies for different error types"""
    RETRY = "RETRY"
    SKIP = "SKIP"
    QUARANTINE = "QUARANTINE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    CIRCUIT_BREAK = "CIRCUIT_BREAK"
    FAILOVER = "FAILOVER"

@dataclass
class ErrorContext:
    """Context information for error handling"""
    operation: str
    component: str
    document_id: Optional[str] = None
    user_id: str = "system"
    session_id: str = "unknown"
    additional_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 3
    last_retry_at: Optional[datetime] = None
    resolved: bool = False
    resolution: Optional[str] = None

@dataclass
class RecoveryAction:
    """Action to take for error recovery"""
    strategy: RecoveryStrategy
    delay_seconds: int = 0
    new_operation: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""

class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_call_allowed(self) -> bool:
        """Check if call is allowed through circuit breaker"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self.last_failure_time and (datetime.utcnow() - self.last_failure_time).seconds > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self) -> None:
        """Record successful operation"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
        self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class RetryConfig:
    """Configuration for retry mechanisms"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter to prevent thundering herd
            jitter_amount = delay * 0.1
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

class DeadLetterQueue:
    """Dead letter queue for unrecoverable errors"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        self._initialize_dlq()

    def _initialize_dlq(self) -> None:
        """Initialize dead letter queue table"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS master.dead_letter_queue (
                        id BIGSERIAL PRIMARY KEY,
                        error_id VARCHAR(255) NOT NULL,
                        error_type VARCHAR(100) NOT NULL,
                        error_message TEXT NOT NULL,
                        severity VARCHAR(50) NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        context JSONB NOT NULL,
                        stack_trace TEXT,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        first_occurrence TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_occurrence TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'PENDING_REVIEW',
                        assigned_to VARCHAR(255),
                        resolution_notes TEXT,
                        resolved_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dlq_status
                    ON master.dead_letter_queue(status)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dlq_category
                    ON master.dead_letter_queue(category)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dlq_severity
                    ON master.dead_letter_queue(severity)
                """)
            self.connection.commit()
            logger.info("Dead letter queue initialized")
        except Exception as e:
            logger.error(f"Failed to initialize dead letter queue: {e}")
            raise

    def add_item(self, error_record: ErrorRecord) -> bool:
        """Add item to dead letter queue"""
        if not self.connection:
            self._initialize_dlq()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO master.dead_letter_queue
                    (error_id, error_type, error_message, severity, category, context, stack_trace,
                     retry_count, max_retries, first_occurrence, last_occurrence, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (error_id) DO UPDATE SET
                    retry_count = dead_letter_queue.retry_count + 1,
                    last_occurrence = NOW(),
                    status = CASE
                        WHEN dead_letter_queue.retry_count >= dead_letter_queue.max_retries
                        THEN 'MAX_RETRIES_EXCEEDED'
                        ELSE dead_letter_queue.status
                    END
                """, (
                    error_record.id,
                    error_record.error_type,
                    error_record.error_message,
                    error_record.severity.value,
                    error_record.category.value,
                    json.dumps(error_record.context.__dict__),
                    error_record.stack_trace,
                    error_record.retry_count,
                    error_record.max_retries,
                    error_record.timestamp,
                    datetime.utcnow(),
                    "PENDING_REVIEW"
                ))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add item to dead letter queue: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def get_pending_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending items from dead letter queue"""
        if not self.connection:
            self._initialize_dlq()

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM master.dead_letter_queue
                    WHERE status IN ('PENDING_REVIEW', 'IN_PROGRESS')
                    ORDER BY first_occurrence ASC
                    LIMIT %s
                """, (limit,))

                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get pending items: {e}")
            return []

    def resolve_item(self, error_id: str, resolution: str, assigned_to: str) -> bool:
        """Mark item as resolved"""
        if not self.connection:
            self._initialize_dlq()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE master.dead_letter_queue
                    SET status = 'RESOLVED',
                        resolution_notes = %s,
                        assigned_to = %s,
                        resolved_at = NOW()
                    WHERE error_id = %s
                """, (resolution, assigned_to, error_id))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to resolve dead letter queue item: {e}")
            return False

class ErrorRecoveryManager:
    """Main error recovery management system"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.dead_letter_queue = DeadLetterQueue(db_config)
        self.error_history: List[ErrorRecord] = []

        # Initialize default circuit breakers
        self._initialize_circuit_breakers()

    def _initialize_circuit_breakers(self) -> None:
        """Initialize circuit breakers for different components"""
        components = [
            'database', 'openai_api', 'govinfo_api', 'redis', 'elasticsearch'
        ]

        for component in components:
            self.circuit_breakers[component] = CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=300
            )

    def register_circuit_breaker(self, component: str, **kwargs) -> None:
        """Register circuit breaker for component"""
        self.circuit_breakers[component] = CircuitBreaker(**kwargs)

    def register_retry_config(self, operation: str, config: RetryConfig) -> None:
        """Register retry configuration for operation"""
        self.retry_configs[operation] = config

    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        document: Optional[VectorDocument] = None
    ) -> RecoveryAction:
        """
        Handle error and determine recovery strategy

        Args:
            error: The exception that occurred
            context: Context information about the error
            document: Document being processed (if applicable)

        Returns:
            RecoveryAction with strategy and parameters
        """
        # Create error record
        error_record = self._create_error_record(error, context)

        # Determine error category and severity
        category, severity = self._categorize_error(error, context)

        # Update error record
        error_record.category = category
        error_record.severity = severity

        # Determine recovery strategy
        recovery_action = self._determine_recovery_strategy(error_record, context)

        # Execute recovery action
        self._execute_recovery_action(error_record, recovery_action, document)

        # Log error for monitoring
        self._log_error_for_monitoring(error_record, recovery_action)

        return recovery_action

    def _create_error_record(self, error: Exception, context: ErrorContext) -> ErrorRecord:
        """Create error record from exception and context"""
        return ErrorRecord(
            id=f"err_{int(time.time())}_{random.randint(1000, 9999)}",
            error_type=type(error).__name__,
            error_message=str(error),
            severity=ErrorSeverity.MEDIUM,  # Will be updated by categorization
            category=ErrorCategory.PROCESSING,  # Will be updated by categorization
            context=context,
            stack_trace=traceback.format_exc()
        )

    def _categorize_error(self, error: Exception, context: ErrorContext) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Categorize error and determine severity"""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network errors
        if any(term in error_message for term in ['connection', 'timeout', 'network', 'dns']):
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH

        # Database errors
        if any(term in error_message for term in ['database', 'sql', 'connection pool', 'deadlock']):
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH

        # Validation errors
        if any(term in error_message for term in ['validation', 'invalid', 'format', 'schema']):
            return ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM

        # External API errors
        if any(term in error_message for term in ['api', 'http', 'rate limit', 'unauthorized']):
            return ErrorCategory.EXTERNAL_API, ErrorSeverity.HIGH

        # System errors
        if any(term in error_message for term in ['memory', 'disk', 'permission', 'system']):
            return ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL

        # Default categorization
        return ErrorCategory.PROCESSING, ErrorSeverity.MEDIUM

    def _determine_recovery_strategy(self, error_record: ErrorRecord, context: ErrorContext) -> RecoveryAction:
        """Determine appropriate recovery strategy"""
        # Check circuit breaker
        if context.component in self.circuit_breakers:
            if not self.circuit_breakers[context.component].is_call_allowed():
                return RecoveryAction(
                    strategy=RecoveryStrategy.CIRCUIT_BREAK,
                    delay_seconds=300,  # 5 minutes
                    reason="Circuit breaker is OPEN"
                )

        # Check retry configuration
        retry_config = self.retry_configs.get(context.operation, RetryConfig())

        if error_record.retry_count < retry_config.max_retries:
            delay = retry_config.calculate_delay(error_record.retry_count)
            return RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                delay_seconds=int(delay),
                reason=f"Retry {error_record.retry_count + 1}/{retry_config.max_retries}"
            )

        # Check if error is recoverable
        if error_record.category in [ErrorCategory.VALIDATION, ErrorCategory.PROCESSING]:
            if error_record.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
                return RecoveryAction(
                    strategy=RecoveryStrategy.SKIP,
                    reason="Recoverable error with low/medium severity"
                )

        # Check if document should be quarantined
        if context.document_id and error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            return RecoveryAction(
                strategy=RecoveryStrategy.QUARANTINE,
                reason="High severity error requires quarantine"
            )

        # Default to manual review for complex errors
        return RecoveryAction(
            strategy=RecoveryStrategy.MANUAL_REVIEW,
            reason="Complex error requires manual review"
        )

    def _execute_recovery_action(
        self,
        error_record: ErrorRecord,
        action: RecoveryAction,
        document: Optional[VectorDocument]
    ) -> None:
        """Execute the determined recovery action"""
        try:
            if action.strategy == RecoveryStrategy.RETRY:
                # Update retry count
                error_record.retry_count += 1
                error_record.last_retry_at = datetime.utcnow()

            elif action.strategy == RecoveryStrategy.QUARANTINE:
                # Mark document as quarantined
                if document:
                    document.processing_status = ProcessingStatus.QUARANTINED
                    document.add_error(f"Quarantined: {error_record.error_message}")

            elif action.strategy == RecoveryStrategy.CIRCUIT_BREAK:
                # Record circuit breaker failure
                if error_record.context.component in self.circuit_breakers:
                    self.circuit_breakers[error_record.context.component].record_failure()

            elif action.strategy == RecoveryStrategy.MANUAL_REVIEW:
                # Add to dead letter queue
                self.dead_letter_queue.add_item(error_record)

            # Update error history
            self.error_history.append(error_record)

            # Keep only recent errors (last 1000)
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]

        except Exception as e:
            logger.error(f"Failed to execute recovery action: {e}")

    def _log_error_for_monitoring(self, error_record: ErrorRecord, action: RecoveryAction) -> None:
        """Log error for monitoring and alerting"""
        try:
            # Log to audit system
            audit_manager = get_audit_manager(self.db_config)
            audit_manager.log_event(
                operation="ERROR_RECOVERY",
                table_name="system",
                record_id=error_record.id,
                category=audit_manager.AuditCategory.SYSTEM_OPERATION,
                additional_metadata={
                    'error_type': error_record.error_type,
                    'error_message': error_record.error_message,
                    'severity': error_record.severity.value,
                    'category': error_record.category.value,
                    'recovery_strategy': action.strategy.value,
                    'retry_count': error_record.retry_count,
                    'component': error_record.context.component
                }
            )

            # Log to application logger
            log_level = {
                ErrorSeverity.LOW: logging.DEBUG,
                ErrorSeverity.MEDIUM: logging.INFO,
                ErrorSeverity.HIGH: logging.WARNING,
                ErrorSeverity.CRITICAL: logging.ERROR
            }.get(error_record.severity, logging.INFO)

            logger.log(
                log_level,
                f"Error in {error_record.context.component}: {error_record.error_message}",
                extra={
                    'error_record': error_record.id,
                    'recovery_strategy': action.strategy.value,
                    'retry_count': error_record.retry_count
                }
            )

        except Exception as e:
            logger.error(f"Failed to log error for monitoring: {e}")

    async def execute_with_retry(
        self,
        operation: str,
        func: Callable,
        *args,
        component: str = "unknown",
        document_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute operation with automatic retry and error handling

        Args:
            operation: Name of operation for retry configuration
            func: Function to execute
            component: Component name for circuit breaker
            document_id: Document ID for context
            *args, **kwargs: Arguments for function

        Returns:
            Function result or raises final exception
        """
        retry_config = self.retry_configs.get(operation, RetryConfig())
        last_exception = None

        for attempt in range(retry_config.max_retries + 1):
            try:
                # Check circuit breaker
                if component in self.circuit_breakers:
                    if not self.circuit_breakers[component].is_call_allowed():
                        raise Exception(f"Circuit breaker is OPEN for {component}")

                # Execute function
                result = await asyncio.coroutine(func)(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                # Record success
                if component in self.circuit_breakers:
                    self.circuit_breakers[component].record_success()

                return result

            except Exception as e:
                last_exception = e

                # Create error context
                context = ErrorContext(
                    operation=operation,
                    component=component,
                    document_id=document_id
                )

                # Handle error and get recovery action
                recovery_action = self.handle_error(e, context)

                # If this was the last attempt, raise the exception
                if attempt == retry_config.max_retries:
                    break

                # Wait before retry
                if recovery_action.delay_seconds > 0:
                    await asyncio.sleep(recovery_action.delay_seconds)

        # All retries exhausted, raise final exception
        raise last_exception

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and trends"""
        if not self.error_history:
            return {'message': 'No errors recorded yet'}

        # Group errors by category and severity
        errors_by_category = {}
        errors_by_severity = {}
        errors_by_component = {}

        for error in self.error_history[-1000:]:  # Last 1000 errors
            # By category
            category = error.category.value
            errors_by_category[category] = errors_by_category.get(category, 0) + 1

            # By severity
            severity = error.severity.value
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + 1

            # By component
            component = error.context.component
            errors_by_component[component] = errors_by_component.get(component, 0) + 1

        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(self.error_history[-1000:]),
            'errors_by_category': errors_by_category,
            'errors_by_severity': errors_by_severity,
            'errors_by_component': errors_by_component,
            'circuit_breaker_states': {
                name: cb.state for name, cb in self.circuit_breakers.items()
            },
            'generated_at': datetime.utcnow().isoformat()
        }

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all components"""
        status = {}
        for name, cb in self.circuit_breakers.items():
            status[name] = {
                'state': cb.state,
                'failure_count': cb.failure_count,
                'last_failure': cb.last_failure_time.isoformat() if cb.last_failure_time else None,
                'call_allowed': cb.is_call_allowed()
            }
        return status

    def reset_circuit_breaker(self, component: str) -> bool:
        """Manually reset circuit breaker for component"""
        if component in self.circuit_breakers:
            self.circuit_breakers[component].state = "CLOSED"
            self.circuit_breakers[component].failure_count = 0
            self.circuit_breakers[component].last_failure_time = None
            return True
        return False

# Global error recovery manager instance
_error_recovery_manager: Optional[ErrorRecoveryManager] = None

def get_error_recovery_manager(db_config: Dict[str, Any]) -> ErrorRecoveryManager:
    """Get or create global error recovery manager instance"""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager(db_config)
    return _error_recovery_manager

# Decorator for automatic error handling
def with_error_recovery(
    operation: str,
    component: str = "unknown",
    document_id_param: Optional[str] = None
):
    """Decorator to add automatic error handling to functions"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            manager = get_error_recovery_manager({})

            # Extract document ID if specified
            doc_id = None
            if document_id_param and args:
                doc_id = getattr(args[0], document_id_param, None) if args else None

            return await manager.execute_with_retry(
                operation=operation,
                func=func,
                *args,
                component=component,
                document_id=doc_id,
                **kwargs
            )

        def sync_wrapper(*args, **kwargs):
            manager = get_error_recovery_manager({})

            # Extract document ID if specified
            doc_id = None
            if document_id_param and args:
                doc_id = getattr(args[0], document_id_param, None) if args else None

            return manager.execute_with_retry(
                operation=operation,
                func=func,
                *args,
                component=component,
                document_id=doc_id,
                **kwargs
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Context manager for error handling
@contextmanager
def error_recovery_context(operation: str, component: str, document_id: Optional[str] = None):
    """Context manager for error handling"""
    manager = get_error_recovery_manager({})

    try:
        yield manager
    except Exception as e:
        context = ErrorContext(
            operation=operation,
            component=component,
            document_id=document_id
        )
        manager.handle_error(e, context)
        raise
