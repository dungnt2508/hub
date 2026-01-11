"""
Store Query Metrics Use Case - Save query performance metrics for trending
"""
from typing import Optional
from uuid import UUID

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ..services.metrics_history_service import dba_metrics_history_service


class StoreQueryMetricsUseCase(BaseUseCase):
    """Use case for storing query performance metrics for trending and baseline"""
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute store query metrics.
        
        Args:
            request: Domain request with slots:
                - connection_id: Database connection ID
                - database_type: Database type (postgresql, mysql, sqlserver, etc.)
                - query_hash: Query hash/identifier
                - mean_time_ms: Mean execution time in ms
                - max_time_ms: Max execution time in ms
                - total_calls: Total number of executions
                - rows_examined: Number of rows examined (optional)
                - rows_returned: Number of rows returned (optional)
                - metadata: Additional metadata (optional)
                
        Returns:
            Domain response with stored metric ID
            
        Raises:
            InvalidInputError: If required fields are missing
            DomainError: If storage fails
        """
        try:
            # Extract slots
            connection_id_str = request.slots.get("connection_id")
            database_type = request.slots.get("database_type")
            query_hash = request.slots.get("query_hash")
            mean_time_ms = float(request.slots.get("mean_time_ms", 0))
            max_time_ms = float(request.slots.get("max_time_ms", 0))
            total_calls = int(request.slots.get("total_calls", 1))
            rows_examined = request.slots.get("rows_examined")
            rows_returned = request.slots.get("rows_returned")
            metadata = request.slots.get("metadata", {})
            
            # Validate required fields
            if not connection_id_str:
                raise InvalidInputError("connection_id is required")
            if not database_type:
                raise InvalidInputError("database_type is required")
            if not query_hash:
                raise InvalidInputError("query_hash is required")
            
            # Convert connection_id
            try:
                connection_id = UUID(connection_id_str)
            except (ValueError, TypeError):
                raise InvalidInputError(f"Invalid connection_id format: {connection_id_str}")
            
            # Convert optional int fields
            if rows_examined:
                try:
                    rows_examined = int(rows_examined)
                except (ValueError, TypeError):
                    rows_examined = None
            
            if rows_returned:
                try:
                    rows_returned = int(rows_returned)
                except (ValueError, TypeError):
                    rows_returned = None
            
            logger.info(
                "Storing query metrics",
                extra={
                    "trace_id": request.trace_id,
                    "connection_id": connection_id,
                    "query_hash": query_hash,
                    "mean_time_ms": mean_time_ms,
                }
            )
            
            # Store metric
            metric_id = await dba_metrics_history_service.store_query_metric(
                connection_id=connection_id,
                database_type=database_type,
                query_hash=query_hash,
                mean_time_ms=mean_time_ms,
                max_time_ms=max_time_ms,
                total_calls=total_calls,
                rows_examined=rows_examined,
                rows_returned=rows_returned,
                metadata=metadata,
            )
            
            logger.info(
                "Query metrics stored successfully",
                extra={
                    "trace_id": request.trace_id,
                    "metric_id": metric_id,
                    "connection_id": connection_id,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "metric_id": str(metric_id),
                    "connection_id": str(connection_id),
                    "query_hash": query_hash,
                    "mean_time_ms": mean_time_ms,
                    "stored_at": __import__("datetime").datetime.utcnow().isoformat(),
                },
                message=f"Đã lưu metrics cho query {query_hash}",
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error storing query metrics: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to store query metrics: {e}") from e
