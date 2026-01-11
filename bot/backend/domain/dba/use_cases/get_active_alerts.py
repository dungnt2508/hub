"""
Get Active Alerts Use Case - Retrieve active database alerts
"""
from typing import Optional
from uuid import UUID

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..services.alerting_service import dba_alerting_service


class GetActiveAlertsUseCase(BaseUseCase):
    """Use case for retrieving active database alerts"""
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute get active alerts.
        
        Args:
            request: Domain request with optional slots:
                - connection_id: Filter by specific connection (optional)
                - limit: Maximum number of alerts (default: 100)
                
        Returns:
            Domain response with list of active alerts
            
        Raises:
            InvalidInputError: If parameters are invalid
            DomainError: If retrieval fails
        """
        try:
            # Extract slots
            connection_id_str = request.slots.get("connection_id")
            limit = int(request.slots.get("limit", 100))
            
            # Validate limit
            if limit < 1 or limit > 1000:
                limit = 100
            
            # Convert connection_id if provided
            connection_id = None
            if connection_id_str:
                try:
                    connection_id = UUID(connection_id_str)
                except (ValueError, TypeError):
                    raise InvalidInputError(f"Invalid connection_id format: {connection_id_str}")
            
            logger.info(
                "Retrieving active alerts",
                extra={
                    "trace_id": request.trace_id,
                    "connection_id": connection_id,
                    "limit": limit,
                }
            )
            
            # Get alerts
            alerts = await dba_alerting_service.get_active_alerts(
                connection_id=connection_id,
                limit=limit
            )
            
            alert_count = len(alerts)
            
            logger.info(
                "Active alerts retrieved",
                extra={
                    "trace_id": request.trace_id,
                    "alert_count": alert_count,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "alerts": alerts,
                    "count": alert_count,
                    "connection_filter": str(connection_id) if connection_id else None,
                },
                message=f"Tìm thấy {alert_count} alert đang hoạt động",
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving active alerts: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to retrieve active alerts: {e}") from e
