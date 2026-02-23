"""
Base repository interface
Định nghĩa contract chung cho tất cả repositories
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any


# Type variable cho Entity
EntityType = TypeVar("EntityType")
IDType = TypeVar("IDType")


class BaseRepository(ABC, Generic[EntityType, IDType]):
    """
    Base repository interface
    
    Tất cả repositories phải implement interface này
    Đảm bảo operations cơ bản: CRUD
    """
    
    @abstractmethod
    async def get_by_id(self, id: IDType) -> Optional[EntityType]:
        """
        Lấy entity theo ID
        
        Args:
            id: ID của entity
            
        Returns:
            Entity nếu tìm thấy, None nếu không
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any
    ) -> List[EntityType]:
        """
        Lấy danh sách entities
        
        Args:
            skip: Số lượng bỏ qua (pagination)
            limit: Số lượng tối đa trả về
            **filters: Filters tùy chọn
            
        Returns:
            Danh sách entities
        """
        pass
    
    @abstractmethod
    async def create(self, entity: EntityType) -> EntityType:
        """
        Tạo entity mới
        
        Args:
            entity: Entity cần tạo
            
        Returns:
            Entity đã được tạo (có ID)
        """
        pass
    
    @abstractmethod
    async def update(self, entity: EntityType) -> EntityType:
        """
        Cập nhật entity
        
        Args:
            entity: Entity cần cập nhật
            
        Returns:
            Entity đã được cập nhật
        """
        pass
    
    @abstractmethod
    async def delete(self, id: IDType) -> bool:
        """
        Xóa entity theo ID
        
        Args:
            id: ID của entity cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu không tìm thấy
        """
        pass
    
    @abstractmethod
    async def exists(self, id: IDType) -> bool:
        """
        Kiểm tra entity có tồn tại không
        
        Args:
            id: ID của entity
            
        Returns:
            True nếu tồn tại, False nếu không
        """
        pass
    
    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """
        Đếm số lượng entities
        
        Args:
            **filters: Filters tùy chọn
            
        Returns:
            Số lượng entities
        """
        pass


class ReadOnlyRepository(ABC, Generic[EntityType, IDType]):
    """
    Read-only repository interface
    Dùng cho các repositories chỉ đọc (views, reports, etc.)
    """
    
    @abstractmethod
    async def get_by_id(self, id: IDType) -> Optional[EntityType]:
        """Lấy entity theo ID"""
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any
    ) -> List[EntityType]:
        """Lấy danh sách entities"""
        pass
    
    @abstractmethod
    async def count(self, **filters: Any) -> int:
        """Đếm số lượng entities"""
        pass
