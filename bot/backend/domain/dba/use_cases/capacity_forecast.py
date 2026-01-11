"""
Capacity Forecast Use Case
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.capacity_forecast import CapacityForecast
from ..config import DBAConfig


class CapacityForecastUseCase(BaseUseCase):
    """Use case for capacity forecasting"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for CapacityForecastUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute capacity forecast.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - forecast_days: Forecast period in days (default: 30)
                - connection_string: Database connection string (optional)
                
        Returns:
            Domain response with capacity forecast
            
        Raises:
            InvalidInputError: If db_type is invalid
            DomainError: If forecasting fails
        """
        try:
            # Extract slots
            db_type_str = request.slots.get("db_type", "postgresql")
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            forecast_days = int(request.slots.get("forecast_days", 30))
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Forecasting capacity for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "forecast_days": forecast_days,
                }
            )
            
            # Get database size and growth metrics
            capacity_query = self._get_capacity_query(db_type)
            
            capacity_data = await self.mcp_client.execute_query(
                db_type=db_type,
                query=capacity_query,
                connection_string=connection_string
            )
            
            # Create forecasts
            forecasts = self._generate_forecasts(capacity_data, forecast_days)
            
            # Identify critical forecasts
            critical_forecasts = [
                f for f in forecasts if f.get("status") == "critical"
            ]
            
            warning_forecasts = [
                f for f in forecasts if f.get("status") == "warning"
            ]
            
            message = (
                f"Capacity Forecast cho {db_type.value} trong {forecast_days} ngày: "
                f"{len(critical_forecasts)} critical, {len(warning_forecasts)} warning"
                if critical_forecasts or warning_forecasts
                else f"Capacity Forecast cho {db_type.value} - Tình hình bình thường"
            )
            
            logger.info(
                f"Capacity forecast completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "forecast_count": len(forecasts),
                    "critical_count": len(critical_forecasts),
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "forecasts": forecasts,
                    "critical_forecasts": critical_forecasts,
                    "warning_forecasts": warning_forecasts,
                    "db_type": db_type.value,
                    "forecast_days": forecast_days,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error forecasting capacity: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to forecast capacity: {e}") from e
    
    @staticmethod
    def _get_capacity_query(db_type: DatabaseType) -> str:
        """Get capacity query for database type"""
        if db_type == DatabaseType.POSTGRESQL:
            return """
                SELECT 
                    datname as database_name,
                    pg_database_size(datname) as size_bytes,
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as connections
                FROM pg_database
                WHERE datname NOT IN ('postgres', 'template0', 'template1')
            """
        elif db_type == DatabaseType.MYSQL:
            return """
                SELECT 
                    table_schema as database_name,
                    SUM(data_length + index_length) as size_bytes,
                    SUM(table_rows) as row_count
                FROM information_schema.tables
                WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema')
                GROUP BY table_schema
            """
        elif db_type == DatabaseType.SQLSERVER:
            return """
                SELECT 
                    name as database_name,
                    size * 8192 as size_bytes
                FROM sys.databases
                WHERE database_id > 4
            """
        else:
            return "SELECT 1"
    
    @staticmethod
    def _generate_forecasts(capacity_data: list, forecast_days: int) -> list:
        """
        Generate capacity forecasts based on current data.
        
        Uses DBAConfig centralized thresholds for deterministic forecasting.
        """
        if not capacity_data:
            return []
        
        forecasts = []
        forecast_date = datetime.utcnow() + timedelta(days=forecast_days)
        
        for item in capacity_data:
            current_size = item.get("size_bytes", 0)
            database_name = item.get("database_name", "unknown")
            
            # Use centralized growth rate from DBAConfig
            monthly_growth_rate = DBAConfig.DEFAULT_MONTHLY_GROWTH_RATE
            daily_growth_rate = monthly_growth_rate / 30
            growth_factor = 1 + (daily_growth_rate * forecast_days) / 100
            
            forecasted_size = current_size * growth_factor
            
            # Use centralized capacity thresholds
            typical_max = DBAConfig.DEFAULT_DATABASE_MAX_BYTES
            warning_threshold = typical_max * DBAConfig.CAPACITY_WARNING_THRESHOLD
            critical_threshold = typical_max * DBAConfig.CAPACITY_CRITICAL_THRESHOLD
            
            # Determine status using DBAConfig method
            status = DBAConfig.get_capacity_status(forecasted_size)
            
            # Generate recommendation based on status
            recommendation = None
            if status == "critical":
                recommendation = (
                    f"CRITICAL: {database_name} capacity will exceed 95% in {forecast_days} days. "
                    f"Current: {current_size/(1024**3):.1f}GB, Forecast: {forecasted_size/(1024**3):.1f}GB. "
                    f"Plan expansion immediately."
                )
            elif status == "warning":
                recommendation = (
                    f"WARNING: {database_name} capacity will exceed 80% in {forecast_days} days. "
                    f"Current: {current_size/(1024**3):.1f}GB, Forecast: {forecasted_size/(1024**3):.1f}GB. "
                    f"Plan expansion within 2 weeks."
                )
            
            forecasts.append({
                "database": database_name,
                "metric_name": "database_size",
                "current_value": current_size,
                "current_value_gb": round(current_size / (1024**3), 2),
                "unit": "bytes",
                "forecast_date": forecast_date.isoformat(),
                "forecast_days": forecast_days,
                "forecasted_value": forecasted_size,
                "forecasted_value_gb": round(forecasted_size / (1024**3), 2),
                "growth_rate_percent": daily_growth_rate * forecast_days,
                "monthly_growth_rate": monthly_growth_rate,
                "warning_threshold": warning_threshold,
                "warning_threshold_gb": round(warning_threshold / (1024**3), 2),
                "critical_threshold": critical_threshold,
                "critical_threshold_gb": round(critical_threshold / (1024**3), 2),
                "status": status,
                "recommendation": recommendation,
            })
        
        return forecasts
