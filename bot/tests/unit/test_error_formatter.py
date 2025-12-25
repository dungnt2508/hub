"""
Unit tests for Error Formatter (Task 8)
"""
import pytest
from unittest.mock import patch

from backend.shared.error_formatter import ErrorFormatter, ErrorCode
from backend.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TenantNotFoundError,
    InvalidInputError,
    RouterError,
    RouterTimeoutError,
    ExternalServiceError,
)


class TestErrorFormatter:
    """Test error formatter functionality"""
    
    def test_format_error_basic(self):
        """Test basic error formatting"""
        response = ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
        )
        
        assert response["success"] is False
        assert response["error"] == ErrorCode.INVALID_INPUT.value
        assert "message" in response
        assert response["status_code"] == 400
    
    def test_format_error_with_custom_message(self):
        """Test error formatting with custom message"""
        custom_message = "Custom error message"
        response = ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            custom_message=custom_message,
        )
        
        assert response["message"] == custom_message
    
    def test_format_error_with_request_id(self):
        """Test error formatting with request ID"""
        request_id = "req-123"
        response = ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            request_id=request_id,
        )
        
        assert response["request_id"] == request_id
    
    def test_format_error_with_details(self):
        """Test error formatting with details"""
        details = {"field": "email", "reason": "invalid format"}
        response = ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details,
        )
        
        assert "details" in response
        assert response["details"] == details
    
    def test_format_exception_authentication_error(self):
        """Test formatting AuthenticationError exception"""
        exception = AuthenticationError("Invalid token")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.AUTHENTICATION_FAILED.value
        assert response["status_code"] == 401
    
    def test_format_exception_authorization_error(self):
        """Test formatting AuthorizationError exception"""
        exception = AuthorizationError("Permission denied")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.AUTHORIZATION_FAILED.value
        assert response["status_code"] == 403
    
    def test_format_exception_tenant_not_found(self):
        """Test formatting TenantNotFoundError exception"""
        exception = TenantNotFoundError("Tenant not found")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.TENANT_NOT_FOUND.value
        assert response["status_code"] == 404
    
    def test_format_exception_invalid_input(self):
        """Test formatting InvalidInputError exception"""
        exception = InvalidInputError("Invalid input")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.INVALID_INPUT.value
        assert response["status_code"] == 400
    
    def test_format_exception_timeout(self):
        """Test formatting RouterTimeoutError exception"""
        exception = RouterTimeoutError("Request timeout")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.TIMEOUT.value
        assert response["status_code"] == 504
    
    def test_format_exception_external_service_error(self):
        """Test formatting ExternalServiceError exception"""
        exception = ExternalServiceError("Service unavailable")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.EXTERNAL_SERVICE_ERROR.value
        assert response["status_code"] == 502
    
    def test_format_exception_router_error(self):
        """Test formatting RouterError exception"""
        exception = RouterError("Routing failed")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.ROUTER_ERROR.value
        assert response["status_code"] == 500
    
    def test_format_exception_unknown_error(self):
        """Test formatting unknown exception"""
        exception = ValueError("Unknown error")
        response = ErrorFormatter.format_exception(exception)
        
        assert response["error"] == ErrorCode.INTERNAL_ERROR.value
        assert response["status_code"] == 500


class TestErrorSanitization:
    """Test error message and details sanitization"""
    
    def test_sanitize_message_removes_tenant_id(self):
        """Test that tenant_id is removed from error messages"""
        message = "Error for tenant 123e4567-e89b-12d3-a456-426614174000"
        sanitized = ErrorFormatter._sanitize_message(message)
        
        assert "123e4567-e89b-12d3-a456-426614174000" not in sanitized
        assert "[ID]" in sanitized or "tenant" not in sanitized.lower()
    
    def test_sanitize_message_removes_api_keys(self):
        """Test that API keys are removed from error messages"""
        message = "Error with key abc123def456ghi789jkl012mno345pqr678"
        sanitized = ErrorFormatter._sanitize_message(message)
        
        assert "abc123def456ghi789jkl012mno345pqr678" not in sanitized
        assert "[KEY]" in sanitized
    
    def test_sanitize_message_removes_file_paths(self):
        """Test that file paths are removed from error messages"""
        message = "Error in file C:\\Users\\test\\file.py"
        sanitized = ErrorFormatter._sanitize_message(message)
        
        assert "C:\\Users\\test\\file.py" not in sanitized
        assert "[PATH]" in sanitized
    
    def test_sanitize_message_removes_connection_strings(self):
        """Test that connection strings are removed from error messages"""
        message = "Error connecting to postgresql://user:pass@host:5432/db"
        sanitized = ErrorFormatter._sanitize_message(message)
        
        assert "postgresql://user:pass@host:5432/db" not in sanitized
        assert "[CONNECTION]" in sanitized
    
    def test_sanitize_message_removes_stack_traces(self):
        """Test that stack traces are removed from error messages"""
        message = "Traceback (most recent call last):\n  File \"test.py\", line 1"
        sanitized = ErrorFormatter._sanitize_message(message)
        
        assert "Traceback" not in sanitized
        assert "File" not in sanitized
        assert "Có lỗi xảy ra trong hệ thống." in sanitized
    
    def test_sanitize_details_removes_sensitive_keys(self):
        """Test that sensitive keys are removed from error details"""
        details = {
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_key": "user-key-123",
            "api_key": "api-key-456",
            "password": "secret-password",
            "message": "Error message",
        }
        
        sanitized = ErrorFormatter._sanitize_details(details)
        
        assert sanitized["tenant_id"] == "[REDACTED]"
        assert sanitized["user_key"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["message"] == "Error message"  # Non-sensitive field preserved
    
    def test_sanitize_details_nested_dict(self):
        """Test that nested dicts are sanitized"""
        details = {
            "error": {
                "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_key": "user-key-123",
            },
            "message": "Error message",
        }
        
        sanitized = ErrorFormatter._sanitize_details(details)
        
        assert sanitized["error"]["tenant_id"] == "[REDACTED]"
        assert sanitized["error"]["user_key"] == "[REDACTED]"
        assert sanitized["message"] == "Error message"
    
    def test_format_error_sanitizes_message(self):
        """Test that format_error sanitizes custom messages"""
        response = ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            custom_message="Error for tenant 123e4567-e89b-12d3-a456-426614174000",
        )
        
        assert "123e4567-e89b-12d3-a456-426614174000" not in response["message"]
    
    def test_format_error_sanitizes_details(self):
        """Test that format_error sanitizes details"""
        details = {
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_key": "user-key-123",
            "message": "Error message",
        }
        
        response = ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details,
        )
        
        assert response["details"]["tenant_id"] == "[REDACTED]"
        assert response["details"]["user_key"] == "[REDACTED]"
        assert response["details"]["message"] == "Error message"


class TestErrorLogging:
    """Test error logging with context"""
    
    @patch('backend.shared.error_formatter.logger')
    def test_format_error_logs_with_context(self, mock_logger):
        """Test that format_error logs with context"""
        log_context = {
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "user-123",
            "endpoint": "bot_message",
        }
        
        ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            log_context=log_context,
        )
        
        # Verify logger.error was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Verify log context includes tenant_id (for logging, not response)
        assert "tenant_id" in call_args[1]["extra"]
        assert call_args[1]["extra"]["tenant_id"] == "123e4567-e89b-12d3-a456-426614174000"
    
    @patch('backend.shared.error_formatter.logger')
    def test_format_error_logs_exception(self, mock_logger):
        """Test that format_error logs exception if provided"""
        exception = ValueError("Test error")
        log_context = {
            "exception": exception,
            "endpoint": "bot_message",
        }
        
        ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            log_context=log_context,
        )
        
        # Verify logger.error was called with exc_info
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Verify exc_info is set when exception is in context
        assert call_args[1].get("exc_info") == exception
    
    def test_format_error_no_info_leakage(self):
        """Test that error response doesn't leak sensitive info"""
        log_context = {
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_key": "user-key-123",
            "api_key": "api-key-456",
        }
        
        response = ErrorFormatter.format_error(
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            log_context=log_context,
        )
        
        # Verify sensitive info is NOT in response
        assert "tenant_id" not in response
        assert "user_key" not in response
        assert "api_key" not in response
        
        # Verify response only has standard fields
        assert "success" in response
        assert "error" in response
        assert "message" in response
        assert "status_code" in response

