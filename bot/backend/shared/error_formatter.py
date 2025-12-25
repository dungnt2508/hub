"""
Error Response Formatter - Standardize error handling across the API
Task 8: Standardize error responses and prevent information leakage
"""
from typing import Dict, Any, Optional
from enum import Enum

from .logger import logger
from .exceptions import (
    RouterError,
    InvalidInputError,
    AuthenticationError,
    AuthorizationError,
    TenantNotFoundError,
    RouterTimeoutError,
    ExternalServiceError,
)


class ErrorCode(str, Enum):
    """Standard error codes"""
    # Authentication & Authorization
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    MISSING_TOKEN = "MISSING_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Input Validation
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Tenant & Resource
    TENANT_NOT_FOUND = "TENANT_NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Router Errors
    ROUTER_ERROR = "ROUTER_ERROR"
    ROUTING_FAILED = "ROUTING_FAILED"
    SESSION_ERROR = "SESSION_ERROR"
    
    # External Services
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    
    # System Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    
    # Webhook Errors
    INVALID_WEBHOOK_SIGNATURE = "INVALID_WEBHOOK_SIGNATURE"
    MISSING_WEBHOOK_SIGNATURE = "MISSING_WEBHOOK_SIGNATURE"


class ErrorFormatter:
    """
    Standardized error formatter.
    
    Responsibilities:
    - Format error responses consistently
    - Sanitize error messages (prevent info leakage)
    - Map exceptions to error codes
    - Log errors with context (but don't expose in response)
    """
    
    # User-friendly error messages (no sensitive info)
    ERROR_MESSAGES = {
        ErrorCode.AUTHENTICATION_FAILED: "Xác thực thất bại. Vui lòng đăng nhập lại.",
        ErrorCode.AUTHORIZATION_FAILED: "Bạn không có quyền thực hiện thao tác này.",
        ErrorCode.INVALID_TOKEN: "Token không hợp lệ.",
        ErrorCode.MISSING_TOKEN: "Thiếu token xác thực.",
        ErrorCode.TOKEN_EXPIRED: "Token đã hết hạn. Vui lòng đăng nhập lại.",
        
        ErrorCode.INVALID_INPUT: "Dữ liệu đầu vào không hợp lệ.",
        ErrorCode.MISSING_REQUIRED_FIELD: "Thiếu trường bắt buộc.",
        ErrorCode.INVALID_FORMAT: "Định dạng dữ liệu không đúng.",
        
        ErrorCode.TENANT_NOT_FOUND: "Không tìm thấy tenant.",
        ErrorCode.RESOURCE_NOT_FOUND: "Không tìm thấy tài nguyên.",
        ErrorCode.RESOURCE_ALREADY_EXISTS: "Tài nguyên đã tồn tại.",
        
        ErrorCode.RATE_LIMIT_EXCEEDED: "Vượt quá giới hạn yêu cầu. Vui lòng thử lại sau.",
        
        ErrorCode.ROUTER_ERROR: "Có lỗi xảy ra khi xử lý câu hỏi. Vui lòng thử lại sau.",
        ErrorCode.ROUTING_FAILED: "Không thể xử lý yêu cầu. Vui lòng thử lại sau.",
        ErrorCode.SESSION_ERROR: "Có lỗi xảy ra với phiên làm việc. Vui lòng thử lại sau.",
        
        ErrorCode.EXTERNAL_SERVICE_ERROR: "Dịch vụ bên ngoài đang gặp sự cố. Vui lòng thử lại sau.",
        ErrorCode.SERVICE_UNAVAILABLE: "Dịch vụ tạm thời không khả dụng. Vui lòng thử lại sau.",
        ErrorCode.TIMEOUT: "Yêu cầu quá thời gian chờ. Vui lòng thử lại sau.",
        
        ErrorCode.INTERNAL_ERROR: "Có lỗi hệ thống. Vui lòng thử lại sau.",
        ErrorCode.DATABASE_ERROR: "Có lỗi xảy ra với cơ sở dữ liệu. Vui lòng thử lại sau.",
        ErrorCode.CONFIGURATION_ERROR: "Có lỗi cấu hình hệ thống.",
        
        ErrorCode.INVALID_WEBHOOK_SIGNATURE: "Chữ ký webhook không hợp lệ.",
        ErrorCode.MISSING_WEBHOOK_SIGNATURE: "Thiếu chữ ký webhook.",
    }
    
    @staticmethod
    def format_error(
        error_code: ErrorCode,
        status_code: int = 500,
        custom_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        log_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format error response.
        
        Args:
            error_code: Standard error code
            status_code: HTTP status code
            custom_message: Optional custom message (will be sanitized)
            details: Optional error details (will be sanitized)
            request_id: Optional request ID for correlation
            log_context: Optional context for logging (NOT included in response)
        
        Returns:
            Standardized error response dict
        """
        # Get user-friendly message
        message = custom_message or ErrorFormatter.ERROR_MESSAGES.get(error_code, "Có lỗi xảy ra.")
        
        # Sanitize message (remove sensitive info)
        message = ErrorFormatter._sanitize_message(message)
        
        # Build response
        response = {
            "success": False,
            "error": error_code.value,
            "message": message,
            "status_code": status_code,
        }
        
        # Add request_id if provided
        if request_id:
            response["request_id"] = request_id
        
        # Add sanitized details if provided
        if details:
            sanitized_details = ErrorFormatter._sanitize_details(details)
            if sanitized_details:
                response["details"] = sanitized_details
        
        # Log error with full context (but don't include in response)
        if log_context:
            logger.error(
                f"Error: {error_code.value}",
                extra={
                    **log_context,
                    "error_code": error_code.value,
                    "status_code": status_code,
                    "request_id": request_id,
                },
                exc_info=log_context.get("exception")
            )
        
        return response
    
    @staticmethod
    def format_exception(
        exception: Exception,
        status_code: int = 500,
        request_id: Optional[str] = None,
        log_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format exception to error response.
        
        Args:
            exception: Exception to format
            status_code: HTTP status code
            request_id: Optional request ID
            log_context: Optional context for logging
        
        Returns:
            Standardized error response dict
        """
        # Map exception to error code
        error_code, status = ErrorFormatter._map_exception_to_error(exception)
        
        # Use provided status_code or mapped status
        final_status = status_code if status_code != 500 else status
        
        # Extract message from exception (will be sanitized)
        custom_message = str(exception) if exception else None
        
        # Add exception to log context
        log_ctx = log_context or {}
        log_ctx["exception"] = exception
        
        return ErrorFormatter.format_error(
            error_code=error_code,
            status_code=final_status,
            custom_message=custom_message,
            request_id=request_id,
            log_context=log_ctx,
        )
    
    @staticmethod
    def _map_exception_to_error(exception: Exception) -> tuple[ErrorCode, int]:
        """
        Map exception to error code and status code.
        
        Returns:
            Tuple of (ErrorCode, HTTP status code)
        """
        if isinstance(exception, AuthenticationError):
            return ErrorCode.AUTHENTICATION_FAILED, 401
        elif isinstance(exception, AuthorizationError):
            return ErrorCode.AUTHORIZATION_FAILED, 403
        elif isinstance(exception, TenantNotFoundError):
            return ErrorCode.TENANT_NOT_FOUND, 404
        elif isinstance(exception, InvalidInputError):
            return ErrorCode.INVALID_INPUT, 400
        elif isinstance(exception, RouterTimeoutError):
            return ErrorCode.TIMEOUT, 504
        elif isinstance(exception, ExternalServiceError):
            return ErrorCode.EXTERNAL_SERVICE_ERROR, 502
        elif isinstance(exception, RouterError):
            return ErrorCode.ROUTER_ERROR, 500
        else:
            return ErrorCode.INTERNAL_ERROR, 500
    
    @staticmethod
    def _sanitize_message(message: str) -> str:
        """
        Sanitize error message to prevent information leakage.
        
        Removes:
        - tenant_id
        - user_key
        - API keys
        - Database connection strings
        - Internal file paths
        - Stack traces
        """
        if not message:
            return message
        
        # Remove sensitive patterns
        import re
        
        # Remove UUIDs that might be tenant_id or user_key
        message = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '[ID]', message, flags=re.IGNORECASE)
        
        # Remove API keys (long alphanumeric strings)
        message = re.sub(r'\b[a-zA-Z0-9]{32,}\b', '[KEY]', message)
        
        # Remove file paths
        message = re.sub(r'[a-zA-Z]:\\[^\s]+|/[^\s]+', '[PATH]', message)
        
        # Remove connection strings
        message = re.sub(r'(postgresql|mysql|mongodb)://[^\s]+', '[CONNECTION]', message, flags=re.IGNORECASE)
        
        # Remove stack trace indicators
        if 'Traceback' in message or 'File "' in message:
            return "Có lỗi xảy ra trong hệ thống."
        
        return message
    
    @staticmethod
    def _sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize error details to prevent information leakage.
        
        Removes sensitive fields:
        - tenant_id
        - user_key
        - api_key
        - password
        - secret
        - token
        """
        if not details:
            return {}
        
        sanitized = {}
        sensitive_keys = {
            'tenant_id', 'user_key', 'api_key', 'password', 'secret',
            'token', 'jwt', 'webhook_secret', 'bot_token', 'app_password',
            'connection_string', 'database_url', 'db_password',
        }
        
        for key, value in details.items():
            # Skip sensitive keys
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = ErrorFormatter._sanitize_details(value)
            elif isinstance(value, str):
                sanitized[key] = ErrorFormatter._sanitize_message(value)
            else:
                sanitized[key] = value
        
        return sanitized

