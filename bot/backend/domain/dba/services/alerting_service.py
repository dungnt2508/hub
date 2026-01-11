"""
DBA Alerting Service - Basic alerting for database anomalies

This service generates alerts for:
- Query performance regression
- Capacity exhaustion
- Deadlock detection
- High I/O pressure
- Long-running queries
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
import json

from ....shared.logger import logger
from ....infrastructure.database_client import database_client
from ....shared.exceptions import DatabaseError


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


@dataclass
class Alert:
    """Alert entity"""
    connection_id: UUID
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    status: AlertStatus = AlertStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "id": str(self.id),
            "connection_id": str(self.connection_id),
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DBAAlertingService:
    """
    Service for creating and managing DBA alerts.
    
    Alert types:
    - QUERY_REGRESSION: Query performance degraded
    - CAPACITY_WARNING: Database approaching capacity limit
    - DEADLOCK_DETECTED: Deadlock detected
    - IO_PRESSURE_HIGH: High I/O pressure
    - SLOW_QUERY: Long-running query detected
    - INDEX_FRAGMENTATION: High index fragmentation
    """
    
    def __init__(self):
        """Initialize alerting service"""
        self.db = database_client
    
    async def create_alert(
        self,
        connection_id: UUID,
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Create a new alert.
        
        Args:
            connection_id: Database connection ID
            alert_type: Type of alert (QUERY_REGRESSION, CAPACITY_WARNING, etc.)
            severity: Alert severity level
            title: Alert title
            message: Alert message
            metric_value: Actual metric value that triggered alert
            threshold_value: Threshold that was exceeded
            metadata: Optional metadata
            
        Returns:
            Alert ID
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            pool = self.db.pool
            alert_id = uuid4()
            now = datetime.utcnow()
            
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO dba_alerts (
                        id, connection_id, alert_type, severity, title, message,
                        metric_value, threshold_value, status, metadata,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    alert_id,
                    connection_id,
                    alert_type,
                    severity.value,
                    title,
                    message,
                    metric_value,
                    threshold_value,
                    AlertStatus.ACTIVE.value,
                    json.dumps(metadata or {}),
                    now,
                    now,
                )
                
                logger.info(
                    f"Alert created: {alert_type}",
                    extra={
                        "alert_id": alert_id,
                        "connection_id": connection_id,
                        "severity": severity.value,
                        "alert_type": alert_type,
                    }
                )
                
                return alert_id
                
        except Exception as e:
            logger.error(
                f"Failed to create alert: {e}",
                extra={"connection_id": connection_id},
                exc_info=True
            )
            raise DatabaseError(f"Failed to create alert: {e}") from e
    
    async def get_active_alerts(
        self,
        connection_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get active alerts.
        
        Args:
            connection_id: Optional filter by connection
            limit: Maximum number of alerts
            
        Returns:
            List of active alerts
        """
        try:
            pool = self.db.pool
            
            async with pool.acquire() as conn:
                if connection_id:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM dba_alerts
                        WHERE connection_id = $1 AND status = $2
                        ORDER BY created_at DESC
                        LIMIT $3
                        """,
                        connection_id,
                        AlertStatus.ACTIVE.value,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM dba_alerts
                        WHERE status = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        AlertStatus.ACTIVE.value,
                        limit,
                    )
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}", exc_info=True)
            return []
    
    async def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: Optional[str] = None,
        note: Optional[str] = None
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            acknowledged_by: User who acknowledged
            note: Optional acknowledgment note
            
        Returns:
            True if successful
        """
        try:
            pool = self.db.pool
            
            async with pool.acquire() as conn:
                metadata = json.dumps({
                    "acknowledged_by": acknowledged_by,
                    "acknowledged_at": datetime.utcnow().isoformat(),
                    "note": note,
                })
                
                await conn.execute(
                    """
                    UPDATE dba_alerts
                    SET status = $1, metadata = $2, updated_at = $3
                    WHERE id = $4
                    """,
                    AlertStatus.ACKNOWLEDGED.value,
                    metadata,
                    datetime.utcnow(),
                    alert_id,
                )
                
                logger.info(
                    f"Alert acknowledged",
                    extra={
                        "alert_id": alert_id,
                        "acknowledged_by": acknowledged_by,
                    }
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}", exc_info=True)
            return False
    
    async def resolve_alert(
        self,
        alert_id: UUID,
        resolved_by: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> bool:
        """
        Mark alert as resolved.
        
        Args:
            alert_id: Alert ID
            resolved_by: User who resolved
            resolution: Resolution details
            
        Returns:
            True if successful
        """
        try:
            pool = self.db.pool
            
            async with pool.acquire() as conn:
                metadata = json.dumps({
                    "resolved_by": resolved_by,
                    "resolved_at": datetime.utcnow().isoformat(),
                    "resolution": resolution,
                })
                
                await conn.execute(
                    """
                    UPDATE dba_alerts
                    SET status = $1, metadata = $2, updated_at = $3
                    WHERE id = $4
                    """,
                    AlertStatus.RESOLVED.value,
                    metadata,
                    datetime.utcnow(),
                    alert_id,
                )
                
                logger.info(
                    f"Alert resolved",
                    extra={
                        "alert_id": alert_id,
                        "resolved_by": resolved_by,
                    }
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}", exc_info=True)
            return False
    
    async def check_query_regression(
        self,
        connection_id: UUID,
        query_hash: str,
        current_time_ms: float,
        baseline_time_ms: float,
        threshold_percent: float = 50.0
    ) -> Optional[UUID]:
        """
        Check for query performance regression and create alert if detected.
        
        Args:
            connection_id: Connection ID
            query_hash: Query hash
            current_time_ms: Current execution time
            baseline_time_ms: Baseline execution time
            threshold_percent: Percentage increase to trigger alert (default 50%)
            
        Returns:
            Alert ID if alert created, None otherwise
        """
        if baseline_time_ms <= 0:
            return None
        
        percent_increase = ((current_time_ms - baseline_time_ms) / baseline_time_ms) * 100
        
        if percent_increase >= threshold_percent:
            return await self.create_alert(
                connection_id=connection_id,
                alert_type="QUERY_REGRESSION",
                severity=AlertSeverity.HIGH if percent_increase > 100 else AlertSeverity.MEDIUM,
                title=f"Query Performance Regression Detected",
                message=f"Query {query_hash} performance degraded by {percent_increase:.1f}%",
                metric_value=current_time_ms,
                threshold_value=baseline_time_ms * (1 + threshold_percent / 100),
                metadata={
                    "query_hash": query_hash,
                    "current_time_ms": current_time_ms,
                    "baseline_time_ms": baseline_time_ms,
                    "percent_increase": percent_increase,
                }
            )
        
        return None
    
    async def check_capacity_warning(
        self,
        connection_id: UUID,
        used_percent: float,
        warning_threshold: float = 80.0,
        critical_threshold: float = 95.0
    ) -> Optional[UUID]:
        """
        Check database capacity and create alert if threshold exceeded.
        
        Args:
            connection_id: Connection ID
            used_percent: Percentage of capacity used
            warning_threshold: Trigger warning at this percent
            critical_threshold: Trigger critical at this percent
            
        Returns:
            Alert ID if alert created, None otherwise
        """
        if used_percent >= critical_threshold:
            return await self.create_alert(
                connection_id=connection_id,
                alert_type="CAPACITY_WARNING",
                severity=AlertSeverity.CRITICAL,
                title="Database Capacity Critical",
                message=f"Database capacity at {used_percent:.1f}% - immediate action required",
                metric_value=used_percent,
                threshold_value=critical_threshold,
                metadata={
                    "used_percent": used_percent,
                    "threshold": critical_threshold,
                }
            )
        elif used_percent >= warning_threshold:
            return await self.create_alert(
                connection_id=connection_id,
                alert_type="CAPACITY_WARNING",
                severity=AlertSeverity.HIGH,
                title="Database Capacity Warning",
                message=f"Database capacity at {used_percent:.1f}% - plan expansion",
                metric_value=used_percent,
                threshold_value=warning_threshold,
                metadata={
                    "used_percent": used_percent,
                    "threshold": warning_threshold,
                }
            )
        
        return None


# Global instance
dba_alerting_service = DBAAlertingService()
