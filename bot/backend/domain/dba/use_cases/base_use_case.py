"""
Base Use Case for DBA Domain
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError
from ....shared.logger import logger
from ..config import DBAConfig
from ..gates import (
    ProductionSafetyGate,
    ScopeValidationGate,
    PermissionGate,
    ResponseValidationGate,
)
from ..ports.mcp_client import DatabaseType


class BaseUseCase(ABC):
    """
    Base class for all DBA use cases.
    
    Provides:
    1. Common validation (slots, db_type)
    2. Centralized error handling
    3. Centralized logging
    4. Gate execution (safety, scope, permission)
    5. Response validation
    """
    
    def __init__(self):
        """Initialize base use case with gates"""
        self.production_gate = ProductionSafetyGate()
        self.scope_gate = ScopeValidationGate()
        self.permission_gate = PermissionGate()
        self.response_gate = ResponseValidationGate()
    
    @abstractmethod
    async def _execute_impl(
        self,
        request: DomainRequest,
        db_type: DatabaseType
    ) -> Dict[str, Any]:
        """
        Actual use case implementation.
        
        Must be implemented by subclasses.
        This is called AFTER all gates have passed.
        
        Args:
            request: Domain request
            db_type: Validated database type
            
        Returns:
            Response data dict
        """
        pass
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute use case with full gate checking.
        
        Order:
        1. Validate slots (required)
        2. Validate & parse db_type
        3. Production safety gate
        4. Scope validation gate
        5. Permission check gate
        6. Execute implementation
        7. Validate response
        8. Build response
        
        Args:
            request: Domain request
            
        Returns:
            Domain response
        """
        try:
            # Step 1: Validate required slots
            self._validate_required_slots(request)
            
            # Step 2: Validate and parse db_type
            db_type = self._validate_db_type(request)
            
            # Step 3: Production safety gate
            connection_string = request.slots.get("connection_string")
            database = request.slots.get("database") or request.slots.get("connection_name")
            await self.production_gate.check(request, connection_string, database)
            
            # Step 4: Scope validation gate
            scope = await self.scope_gate.check(request)
            
            # Step 5: Permission check gate
            user_id = request.user_context.get("user_id", "unknown")
            await self.permission_gate.check(
                request.intent,
                user_id,
                request.user_context
            )
            
            # Log start
            self._log_start(request, db_type, scope)
            
            # Step 6: Execute implementation
            result = await self._execute_impl(request, db_type)
            
            # Step 7: Validate response
            response_type = request.intent.replace("analyze_", "").replace("detect_", "").replace("check_", "")
            if result.get("data"):
                self.response_gate.validate_response(
                    response_type,
                    result.get("data"),
                    allow_none=True
                )
            
            # Step 8: Build and return response
            self._log_success(request)
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data=result.get("data", {}),
                message=result.get("message", ""),
            )
        
        except InvalidInputError:
            raise
        except Exception as e:
            self._log_error(request, e)
            raise
    
    def _validate_required_slots(self, request: DomainRequest) -> None:
        """
        Validate required slots.
        
        Subclasses can override to specify custom required slots.
        
        Args:
            request: Domain request
            
        Raises:
            InvalidInputError: If required slots missing
        """
        # Default required slots (all use cases need db_type)
        required_slots = ["db_type"]
        
        missing = self.validate_slots(request, required_slots)
        if missing:
            raise InvalidInputError(f"Missing required slots: {', '.join(missing)}")
    
    def _validate_db_type(self, request: DomainRequest) -> DatabaseType:
        """
        Centralized db_type validation.
        
        Args:
            request: Domain request
            
        Returns:
            Validated DatabaseType
            
        Raises:
            InvalidInputError: If db_type invalid
        """
        db_type_str = request.slots.get("db_type", "postgresql")
        
        try:
            db_type = DatabaseType(db_type_str.lower())
        except ValueError:
            raise InvalidInputError(
                f"Unsupported database type: {db_type_str}. "
                f"Supported types: {[dt.value for dt in DatabaseType]}"
            )
        
        return db_type
    
    def _log_start(self, request: DomainRequest, db_type: DatabaseType, scope: Any = None) -> None:
        """
        Centralized logging - start of use case.
        
        Args:
            request: Domain request
            db_type: Database type
            scope: Scope object (optional)
        """
        logger.info(
            f"Executing {request.intent}",
            extra={
                "trace_id": request.trace_id,
                "intent": request.intent,
                "db_type": db_type.value,
                "database": getattr(scope, "database", None) if scope else None,
                "user_id": request.user_context.get("user_id"),
            }
        )
    
    def _log_success(self, request: DomainRequest) -> None:
        """
        Centralized logging - success.
        
        Args:
            request: Domain request
        """
        logger.info(
            f"Completed {request.intent}",
            extra={
                "trace_id": request.trace_id,
                "intent": request.intent,
                "status": "success",
            }
        )
    
    def _log_error(self, request: DomainRequest, error: Exception) -> None:
        """
        Centralized logging - error.
        
        Args:
            request: Domain request
            error: Exception
        """
        logger.error(
            f"Error in {request.intent}: {str(error)}",
            extra={
                "trace_id": request.trace_id,
                "intent": request.intent,
            },
            exc_info=True
        )
    
    def validate_slots(
        self,
        request: DomainRequest,
        required_slots: list
    ) -> list:
        """
        Validate required slots.
        
        Args:
            request: Domain request
            required_slots: List of required slot names
            
        Returns:
            List of missing slot names
        """
        missing = []
        for slot in required_slots:
            if slot not in request.slots or request.slots[slot] is None:
                missing.append(slot)
        return missing

