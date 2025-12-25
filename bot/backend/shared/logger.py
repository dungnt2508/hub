"""
Structured Logging Setup
Task 9: Enhanced structured logging with tenant_id and request correlation
"""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
import contextvars

# Context variables for request correlation
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('request_id', default=None)
trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id', default=None)
tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('tenant_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON structured formatter with tenant_id and request correlation.
    
    Task 9: Ensures tenant_id, request_id, and trace_id are included in all log entries.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with context variables"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Task 9.1: Add tenant_id from context if available
        tenant_id = tenant_id_var.get()
        if tenant_id:
            log_data["tenant_id"] = tenant_id
        
        # Task 9.2: Add request_id/trace_id correlation
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        trace_id = trace_id_var.get()
        if trace_id:
            log_data["trace_id"] = trace_id
        
        # Add extra fields if present (may override context vars)
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)
        
        # Ensure tenant_id is always present (from extra or context)
        if "tenant_id" not in log_data:
            # Try to get from record attributes
            if hasattr(record, "tenant_id"):
                log_data["tenant_id"] = record.tenant_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup structured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    
    return logger


def set_logging_context(
    tenant_id: Optional[str] = None,
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
):
    """
    Set logging context for current request.
    
    Task 9: Set context variables that will be included in all log entries.
    
    Args:
        tenant_id: Tenant ID
        request_id: Request ID for correlation
        trace_id: Trace ID for distributed tracing
    """
    if tenant_id:
        tenant_id_var.set(tenant_id)
    if request_id:
        request_id_var.set(request_id)
    if trace_id:
        trace_id_var.set(trace_id)


def clear_logging_context():
    """Clear logging context"""
    tenant_id_var.set(None)
    request_id_var.set(None)
    trace_id_var.set(None)


# Global logger instance
logger = setup_logger("bot service")

