"""
Exceptions tùy chỉnh cho toàn hệ thống
Tất cả exceptions đều có message tiếng Việt
"""
from typing import Any, Optional


class BaseException(Exception):
    """Base exception cho tất cả custom exceptions"""
    
    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception sang dict để serialize"""
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# ==================== DOMAIN EXCEPTIONS ====================

class DomainException(BaseException):
    """Base exception cho domain layer"""
    pass


class EntityNotFoundError(DomainException):
    """Entity không tìm thấy"""
    
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} với ID {entity_id} không tìm thấy",
            code="ENTITY_NOT_FOUND",
            details={"entity": entity_name, "id": str(entity_id)}
        )


class EntityAlreadyExistsError(DomainException):
    """Entity đã tồn tại"""
    
    def __init__(self, entity_name: str, field: str, value: Any):
        super().__init__(
            message=f"{entity_name} với {field}={value} đã tồn tại",
            code="ENTITY_ALREADY_EXISTS",
            details={"entity": entity_name, "field": field, "value": str(value)}
        )


class BusinessRuleViolationError(DomainException):
    """Vi phạm quy tắc nghiệp vụ"""
    
    def __init__(self, rule: str, reason: str):
        super().__init__(
            message=f"Vi phạm quy tắc nghiệp vụ: {rule}. Lý do: {reason}",
            code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule, "reason": reason}
        )


class InvalidStateError(DomainException):
    """Trạng thái không hợp lệ"""
    
    def __init__(self, entity: str, current_state: str, action: str):
        super().__init__(
            message=f"Không thể thực hiện '{action}' khi {entity} đang ở trạng thái '{current_state}'",
            code="INVALID_STATE",
            details={"entity": entity, "current_state": current_state, "action": action}
        )


# ==================== APPLICATION EXCEPTIONS ====================

class ApplicationException(BaseException):
    """Base exception cho application layer"""
    pass


class ValidationError(ApplicationException):
    """Lỗi validation dữ liệu đầu vào"""
    
    def __init__(self, field: str, message: str, value: Any = None):
        super().__init__(
            message=f"Lỗi validation trường '{field}': {message}",
            code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value else None}
        )


class AuthenticationError(ApplicationException):
    """Lỗi xác thực"""
    
    def __init__(self, message: str = "Xác thực thất bại"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(ApplicationException):
    """Lỗi phân quyền"""
    
    def __init__(self, message: str = "Bạn không có quyền truy cập tài nguyên này"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR"
        )


class UseCaseError(ApplicationException):
    """Lỗi trong quá trình thực thi use case"""
    
    def __init__(self, usecase_name: str, reason: str):
        super().__init__(
            message=f"Lỗi khi thực thi {usecase_name}: {reason}",
            code="USECASE_ERROR",
            details={"usecase": usecase_name, "reason": reason}
        )


# ==================== INFRASTRUCTURE EXCEPTIONS ====================

class InfrastructureException(BaseException):
    """Base exception cho infrastructure layer"""
    pass


class DatabaseError(InfrastructureException):
    """Lỗi database"""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Lỗi database khi thực hiện '{operation}': {reason}",
            code="DATABASE_ERROR",
            details={"operation": operation, "reason": reason}
        )


class ConcurrentUpdateError(DatabaseError):
    """Lỗi cập nhật đồng thời (Optimistic Locking)"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            operation="update",
            reason=f"Tài nguyên {resource} với ID {resource_id} đã bị thay đổi bởi luồng khác."
        )


class CacheError(InfrastructureException):
    """Lỗi cache"""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Lỗi cache khi thực hiện '{operation}': {reason}",
            code="CACHE_ERROR",
            details={"operation": operation, "reason": reason}
        )


class ExternalServiceError(InfrastructureException):
    """Lỗi khi gọi service bên ngoài"""
    
    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"Lỗi khi gọi service '{service}': {reason}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "reason": reason}
        )


class AIModelError(InfrastructureException):
    """Lỗi AI model"""
    
    def __init__(self, model_or_message: str, operation: str = None, reason: str = None):
        if operation is None and reason is None:
            super().__init__(
                message=model_or_message,
                code="AI_MODEL_ERROR"
            )
        else:
            super().__init__(
                message=f"Lỗi AI model '{model_or_message}' khi thực hiện '{operation}': {reason}",
                code="AI_MODEL_ERROR",
                details={"model": model_or_message, "operation": operation, "reason": reason}
            )


class VectorStoreError(InfrastructureException):
    """Lỗi vector store"""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Lỗi vector store khi thực hiện '{operation}': {reason}",
            code="VECTORSTORE_ERROR",
            details={"operation": operation, "reason": reason}
        )


# ==================== INTERFACE EXCEPTIONS ====================

class InterfaceException(BaseException):
    """Base exception cho interface layer"""
    pass


class InvalidRequestError(InterfaceException):
    """Request không hợp lệ"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Request không hợp lệ: {message}",
            code="INVALID_REQUEST",
            details=details
        )


class ResourceNotFoundError(InterfaceException):
    """Resource không tìm thấy (HTTP 404)"""
    
    def __init__(self, resource: str):
        super().__init__(
            message=f"Không tìm thấy tài nguyên: {resource}",
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource}
        )


# ==================== UTILITY FUNCTIONS ====================

def is_domain_error(exc: Exception) -> bool:
    """Kiểm tra có phải lỗi domain không"""
    return isinstance(exc, DomainException)


def is_application_error(exc: Exception) -> bool:
    """Kiểm tra có phải lỗi application không"""
    return isinstance(exc, ApplicationException)


def is_infrastructure_error(exc: Exception) -> bool:
    """Kiểm tra có phải lỗi infrastructure không"""
    return isinstance(exc, InfrastructureException)
