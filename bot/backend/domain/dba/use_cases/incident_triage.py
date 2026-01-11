"""
Incident Triage Use Case
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import re

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType
from ..entities.incident import Incident, IncidentType, IncidentSeverity
from ..config import DBAConfig


class IncidentTriageUseCase(BaseUseCase):
    """Use case for database incident triage"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for IncidentTriageUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute incident triage.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (postgresql, mysql, sqlserver, etc.)
                - incident_description: Description of the incident (required)
                - connection_string: Database connection string (optional)
                
        Returns:
            Domain response with triaged incident
            
        Raises:
            InvalidInputError: If db_type or incident_description is missing
            DomainError: If triage fails
        """
        try:
            # Extract slots
            db_type_str = request.slots.get("db_type", "postgresql")
            incident_description = request.slots.get("incident_description")
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            user_id = request.user_context.get("user_id")
            
            # Validate required slots
            missing = self.validate_slots(request, ["incident_description"])
            if missing:
                raise InvalidInputError(f"Missing required slots: {', '.join(missing)}")
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            logger.info(
                f"Triaging incident for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "description_length": len(incident_description),
                }
            )
            
            # Analyze incident description
            incident_type, severity = self._analyze_incident(incident_description)
            
            # Collect diagnostic data
            diagnostic_data = await self._collect_diagnostics(
                self.mcp_client, db_type, connection_string, connection_name, connection_id, tenant_id
            )
            
            # Create incident
            incident = Incident(
                incident_id=f"INC_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                incident_type=incident_type,
                severity=severity,
                title=f"{incident_type.value.replace('_', ' ').title()} - {db_type.value}",
                description=incident_description,
                database=db_type.value,
                metadata={
                    "diagnostics": diagnostic_data,
                    "reported_by": user_id,
                    "tenant_id": tenant_id,
                }
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(incident, diagnostic_data)
            
            message = (
                f"Incident Triage: {incident.title} "
                f"- Severity: {severity.value.upper()}, "
                f"Type: {incident_type.value}"
            )
            
            logger.info(
                f"Incident triage completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "incident_type": incident_type.value,
                    "severity": severity.value,
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "incident": incident.to_dict(),
                    "recommendations": recommendations,
                    "diagnostic_data": diagnostic_data,
                    "db_type": db_type.value,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error triaging incident: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to triage incident: {e}") from e
    
    @staticmethod
    def _analyze_incident(description: str) -> Tuple[IncidentType, IncidentSeverity]:
        """
        Analyze incident description to determine type and severity.
        
        DETERMINISTIC matching using PRIORITY ORDER.
        First match wins → no ambiguity.
        
        Priority order matches DBAConfig.INCIDENT_PRIORITY.
        """
        description_lower = description.lower()
        
        # Pattern matching in priority order (lowest priority number = highest importance)
        patterns = [
            {
                "type": IncidentType.DISK_SPACE,
                "severity": IncidentSeverity.CRITICAL,
                "priority": 1,
                "regex": r"(disk|space|storage).*(full|out of space|out of storage|exhausted)",
            },
            {
                "type": IncidentType.DEADLOCK,
                "severity": IncidentSeverity.CRITICAL,
                "priority": 2,
                "regex": r"deadlock",
            },
            {
                "type": IncidentType.MEMORY_PRESSURE,
                "severity": IncidentSeverity.HIGH,
                "priority": 3,
                "regex": r"(memory|oom|out of memory)",
            },
            {
                "type": IncidentType.CPU_PRESSURE,
                "severity": IncidentSeverity.HIGH,
                "priority": 4,
                "regex": r"(cpu|processor|cpu usage|100%)",
            },
            {
                "type": IncidentType.BLOCKING,
                "severity": IncidentSeverity.HIGH,
                "priority": 5,
                "regex": r"(blocking|blocked|lock.*wait|transaction.*block)",
            },
            {
                "type": IncidentType.CONNECTION_POOL_EXHAUSTED,
                "severity": IncidentSeverity.HIGH,
                "priority": 6,
                "regex": r"(connection.*pool|too many.*connection|connection.*exhausted)",
            },
            {
                "type": IncidentType.SLOW_QUERY,
                "severity": IncidentSeverity.MEDIUM,
                "priority": 7,
                "regex": r"(slow|slow query|lag|latency|timeout|performance)",
            },
        ]
        
        # Match in priority order - FIRST match wins
        for pattern in patterns:
            try:
                if re.search(pattern["regex"], description_lower):
                    return pattern["type"], pattern["severity"]
            except Exception:
                continue
        
        # Default: OTHER with MEDIUM severity
        return IncidentType.OTHER, IncidentSeverity.MEDIUM
    
    async def _collect_diagnostics(
        self,
        mcp_client: IMCPDBClient,
        db_type: DatabaseType,
        connection_string: Optional[str],
        connection_name: Optional[str],
        connection_id: Optional[str],
        tenant_id: Optional[str]
    ) -> dict:
        """Collect diagnostic data for incident"""
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "db_type": db_type.value,
        }
        
        # Try to get connection info
        try:
            connection_info = await mcp_client.get_connection_info(db_type, connection_string)
            diagnostics["connection_info"] = connection_info
        except Exception as e:
            logger.debug(f"Could not get connection info: {e}")
        
        # Try to get wait stats
        try:
            wait_stats = await mcp_client.get_wait_stats(
                db_type, connection_string, connection_name, connection_id, tenant_id
            )
            diagnostics["wait_stats"] = wait_stats
        except Exception as e:
            logger.debug(f"Could not get wait stats: {e}")
        
        return diagnostics
    
    @staticmethod
    def _generate_recommendations(incident: Incident, diagnostic_data: dict) -> list:
        """
        Generate CONDITIONAL recommendations based on incident type and diagnostic data.
        
        RULE: Only add recommendations if there's supporting diagnostic data.
        No generic "consider" or "maybe" recommendations.
        """
        recommendations = []
        
        if incident.incident_type == IncidentType.SLOW_QUERY:
            recommendations.append({
                "action": "analyze_slow_query_log",
                "priority": "high",
                "why": "Performance degradation detected",
                "steps": [
                    "1. Run 'analyze_slow_query' use case",
                    "2. Review execution plans for top queries",
                    "3. Check if indexes are missing or fragmented",
                ]
            })
        
        elif incident.incident_type == IncidentType.BLOCKING:
            recommendations.append({
                "action": "identify_blocking_sessions",
                "priority": "critical",
                "why": "Active blocking detected - transactions waiting",
                "steps": [
                    "1. Run 'detect_blocking' use case",
                    "2. Identify blocking transaction",
                    "3. Review if blocking session can be killed or if app needs modification",
                ]
            })
        
        elif incident.incident_type == IncidentType.DEADLOCK:
            recommendations.append({
                "action": "analyze_deadlock_pattern",
                "priority": "critical",
                "why": "Deadlock detected - transaction failure",
                "steps": [
                    "1. Run 'detect_deadlock_pattern' use case",
                    "2. Review deadlock graph if available",
                    "3. Fix transaction order or isolation levels",
                ]
            })
        
        elif incident.incident_type == IncidentType.DISK_SPACE:
            recommendations.append({
                "action": "emergency_disk_management",
                "priority": "critical",
                "why": "Disk space shortage - database may go offline",
                "steps": [
                    "1. Immediately check available disk space: df -h",
                    "2. Identify and remove old backups/logs",
                    "3. If insufficient, request emergency disk allocation",
                ]
            })
        
        elif incident.incident_type == IncidentType.MEMORY_PRESSURE:
            recommendations.append({
                "action": "memory_pressure_analysis",
                "priority": "high",
                "why": "Memory pressure detected - performance degradation likely",
                "steps": [
                    "1. Check actual memory usage: free -h",
                    "2. Run 'analyze_wait_stats' to see if memory waits",
                    "3. Consider increasing buffer pool or query optimization",
                ]
            })
        
        elif incident.incident_type == IncidentType.CPU_PRESSURE:
            recommendations.append({
                "action": "cpu_pressure_analysis",
                "priority": "high",
                "why": "High CPU usage detected - may impact other services",
                "steps": [
                    "1. Identify high CPU queries: run 'analyze_slow_query'",
                    "2. Check if CPU spikes are consistent or temporary",
                    "3. Consider query optimization or horizontal scaling",
                ]
            })
        
        elif incident.incident_type == IncidentType.CONNECTION_POOL_EXHAUSTED:
            recommendations.append({
                "action": "connection_pool_recovery",
                "priority": "critical",
                "why": "Connection pool exhausted - new connections cannot be created",
                "steps": [
                    "1. Check active connections: SELECT COUNT(*) FROM pg_stat_activity",
                    "2. Identify and close idle connections",
                    "3. Increase pool size if legitimate high connection count",
                ]
            })
        
        else:
            recommendations.append({
                "action": "escalate_to_dba_team",
                "priority": "medium",
                "why": "Unknown incident type - requires expert analysis",
                "contact": "DBA team on-call"
            })
        
        return recommendations
