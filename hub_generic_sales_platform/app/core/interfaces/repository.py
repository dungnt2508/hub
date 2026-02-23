"""Core Repository Interface - Port trong Hexagonal Architecture"""

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from abc import ABC, abstractmethod

T = TypeVar("T")


class IRepository(Generic[T], ABC):
    """Interface cơ sở cho tất cả các repositories"""
    
    @abstractmethod
    async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[T]:
        """Lấy một thực thể theo ID"""
        pass
    
    @abstractmethod
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        **filters
    ) -> List[T]:
        """Lấy danh sách nhiều thực thể"""
        pass
    
    @abstractmethod
    async def create(self, obj_in: Dict[str, Any], tenant_id: Optional[str] = None) -> T:
        """Tạo mới một thực thể"""
        pass
    
    @abstractmethod
    async def update(
        self,
        db_obj: T,
        obj_in: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> T:
        """Cập nhật thực thể"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        id: str,
        tenant_id: Optional[str] = None
    ) -> Optional[T]:
        """Xóa thực thể"""
        pass
