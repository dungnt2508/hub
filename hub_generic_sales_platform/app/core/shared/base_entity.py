"""
Base entity cho domain layer
Tất cả entities trong domain phải kế thừa từ BaseEntity
"""
from datetime import datetime
from typing import Any, Optional
from abc import ABC
from app.core.shared.datetime_utils import utc_now


class BaseEntity(ABC):
    """
    Base class cho tất cả domain entities
    
    Đặc điểm:
    - Có identity (id)
    - Có audit fields (created_at, updated_at)
    - Immutable sau khi tạo (chỉ update qua methods)
    - Business logic nằm trong entity
    """
    
    def __init__(
        self,
        id: Optional[Any] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = id
        self._created_at = created_at or utc_now()
        self._updated_at = updated_at or utc_now()
    
    @property
    def id(self) -> Optional[Any]:
        """ID của entity"""
        return self._id
    
    @property
    def created_at(self) -> datetime:
        """Thời gian tạo"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Thời gian cập nhật lần cuối"""
        return self._updated_at
    
    def mark_updated(self) -> None:
        """Đánh dấu entity đã được update"""
        self._updated_at = utc_now()
    
    def __eq__(self, other: object) -> bool:
        """So sánh 2 entities dựa trên ID"""
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id and self.id is not None
    
    def __hash__(self) -> int:
        """Hash dựa trên ID"""
        return hash(self.id) if self.id else hash(id(self))
    
    def __repr__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}(id={self.id})"


class AggregateRoot(BaseEntity):
    """
    Aggregate Root - entity đứng đầu của aggregate
    
    Đặc điểm:
    - Quản lý toàn bộ lifecycle của aggregate
    - Có thể raise domain events
    - Đảm bảo business invariants
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._domain_events: list[Any] = []
    
    @property
    def domain_events(self) -> list[Any]:
        """Danh sách domain events đã raise"""
        return self._domain_events.copy()
    
    def raise_event(self, event: Any) -> None:
        """Raise một domain event"""
        self._domain_events.append(event)
    
    def clear_events(self) -> None:
        """Xóa tất cả domain events"""
        self._domain_events.clear()


class ValueObject(ABC):
    """
    Value Object - thực thể không có identity
    
    Đặc điểm:
    - Không có ID
    - So sánh dựa trên giá trị
    - Immutable
    - Có thể dùng như attribute của Entity
    """
    
    def __eq__(self, other: object) -> bool:
        """So sánh dựa trên tất cả attributes"""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
    
    def __hash__(self) -> int:
        """Hash dựa trên tất cả attributes"""
        return hash(tuple(sorted(self.__dict__.items())))
    
    def __repr__(self) -> str:
        """String representation"""
        attrs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"
