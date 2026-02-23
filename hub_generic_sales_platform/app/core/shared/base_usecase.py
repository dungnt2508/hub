"""
Base use case
Định nghĩa pattern chung cho tất cả use cases
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from app.core.shared.logger import LoggerMixin


# Type variables
InputDTO = TypeVar("InputDTO")
OutputDTO = TypeVar("OutputDTO")


class BaseUseCase(ABC, LoggerMixin, Generic[InputDTO, OutputDTO]):
    """
    Base use case
    
    Tất cả use cases phải kế thừa từ class này
    Pattern: Command pattern với input/output rõ ràng
    """
    
    @abstractmethod
    async def execute(self, input_dto: InputDTO) -> OutputDTO:
        """
        Thực thi use case
        
        Args:
            input_dto: Dữ liệu đầu vào (DTO)
            
        Returns:
            Dữ liệu đầu ra (DTO)
            
        Raises:
            UseCaseError: Khi có lỗi trong quá trình thực thi
        """
        pass
    
    async def __call__(self, input_dto: InputDTO) -> OutputDTO:
        """
        Cho phép gọi use case như function
        
        Example:
            result = await create_user_usecase(input_data)
        """
        self.logger.info(
            f"Bắt đầu thực thi use case",
            usecase=self.__class__.__name__,
            input_type=type(input_dto).__name__
        )
        
        try:
            result = await self.execute(input_dto)
            
            self.logger.info(
                f"Thực thi use case thành công",
                usecase=self.__class__.__name__,
                output_type=type(result).__name__
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Lỗi khi thực thi use case",
                usecase=self.__class__.__name__,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise


class BaseQueryUseCase(ABC, LoggerMixin, Generic[InputDTO, OutputDTO]):
    """
    Base query use case (CQRS pattern)
    
    Dành cho các use case chỉ đọc dữ liệu (query)
    Không thay đổi state của hệ thống
    """
    
    @abstractmethod
    async def query(self, input_dto: InputDTO) -> OutputDTO:
        """
        Thực hiện query
        
        Args:
            input_dto: Dữ liệu đầu vào
            
        Returns:
            Kết quả query
        """
        pass
    
    async def __call__(self, input_dto: InputDTO) -> OutputDTO:
        """Gọi query như function"""
        self.logger.debug(
            f"Thực hiện query",
            usecase=self.__class__.__name__
        )
        return await self.query(input_dto)


class BaseCommandUseCase(ABC, LoggerMixin, Generic[InputDTO, OutputDTO]):
    """
    Base command use case (CQRS pattern)
    
    Dành cho các use case thay đổi state (command)
    Có thể raise domain events
    """
    
    @abstractmethod
    async def execute(self, input_dto: InputDTO) -> OutputDTO:
        """
        Thực thi command
        
        Args:
            input_dto: Dữ liệu đầu vào
            
        Returns:
            Kết quả thực thi
        """
        pass
    
    async def __call__(self, input_dto: InputDTO) -> OutputDTO:
        """Gọi command như function"""
        self.logger.info(
            f"Thực thi command",
            usecase=self.__class__.__name__
        )
        
        try:
            result = await self.execute(input_dto)
            
            self.logger.info(
                f"Command thành công",
                usecase=self.__class__.__name__
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Lỗi khi thực thi command",
                usecase=self.__class__.__name__,
                error=str(e),
                exc_info=True
            )
            raise
