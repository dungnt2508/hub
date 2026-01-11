"""
Compare sp_Blitz vs Custom Analysis Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType


class CompareSPBlitzVsCustomUseCase(BaseUseCase):
    """Use case for comparing sp_Blitz results with custom analysis"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for CompareSPBlitzVsCustomUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute compare sp_Blitz vs custom.
        
        Args:
            request: Domain request with slots:
                - db_type: Database type (sqlserver, mysql, postgresql, etc.)
                - run_blitz: Whether to run sp_Blitz (default: True)
                - connection_string: Database connection string (optional)
                
        Returns:
            Domain response with comparison results
            
        Raises:
            InvalidInputError: If db_type is invalid
            DomainError: If comparison fails
        """
        try:
            # Extract slots
            db_type_str = request.slots.get("db_type", "sqlserver")
            run_blitz = request.slots.get("run_blitz", True)
            connection_string = request.slots.get("connection_string")
            connection_name = request.slots.get("connection_name")
            connection_id = request.slots.get("connection_id")
            tenant_id = request.user_context.get("tenant_id")
            
            # Validate db_type
            try:
                db_type = DatabaseType(db_type_str.lower())
            except ValueError:
                raise InvalidInputError(
                    f"Unsupported database type: {db_type_str}. "
                    f"Supported types: {[dt.value for dt in DatabaseType]}"
                )
            
            # sp_Blitz only works with SQL Server
            if db_type != DatabaseType.SQLSERVER:
                raise InvalidInputError(
                    f"sp_Blitz only supports SQL Server, got {db_type_str}"
                )
            
            logger.info(
                f"Comparing sp_Blitz vs custom analysis for {db_type.value}",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "run_blitz": run_blitz,
                }
            )
            
            # Get sp_Blitz results if requested
            blitz_results = []
            if run_blitz:
                try:
                    blitz_results = await self._run_sp_blitz(
                        db_type, connection_string, connection_name, connection_id
                    )
                except Exception as e:
                    logger.warning(f"Could not run sp_Blitz: {e}")
            
            # Run custom analysis
            custom_results = await self._run_custom_analysis(
                self.mcp_client, db_type, connection_string, connection_name, connection_id, tenant_id
            )
            
            # Compare results
            comparison = self._compare_results(blitz_results, custom_results)
            
            message = (
                f"Comparison của sp_Blitz vs Custom Analysis cho {db_type.value}: "
                f"sp_Blitz findings: {len(blitz_results)}, "
                f"Custom findings: {len(custom_results)}, "
                f"Common issues: {comparison.get('common_count', 0)}"
            )
            
            logger.info(
                f"Comparison completed",
                extra={
                    "trace_id": request.trace_id,
                    "db_type": db_type.value,
                    "blitz_count": len(blitz_results),
                    "custom_count": len(custom_results),
                }
            )
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                data={
                    "sp_blitz_results": blitz_results,
                    "custom_results": custom_results,
                    "comparison": comparison,
                    "db_type": db_type.value,
                },
                message=message,
            )
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error comparing results: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to compare results: {e}") from e
    
    async def _run_sp_blitz(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str],
        connection_name: Optional[str],
        connection_id: Optional[str]
    ) -> list:
        """Run sp_Blitz analysis"""
        # sp_Blitz is a stored procedure for SQL Server
        blitz_query = """
            EXEC master.dbo.sp_Blitz
                @CheckUserDatabaseObjects = 1,
                @CheckDatabaseMail = 1,
                @CheckServerInfo = 1
        """
        
        try:
            results = await self.mcp_client.execute_query(
                db_type=db_type,
                query=blitz_query,
                connection_string=connection_string
            )
            
            # Parse sp_Blitz results
            parsed_results = []
            for row in results:
                parsed_results.append({
                    "priority": row.get("Priority"),
                    "finding_group": row.get("FindingsGroup"),
                    "finding": row.get("Finding"),
                    "details": row.get("Details"),
                    "source": "sp_Blitz",
                })
            
            return parsed_results
        except Exception as e:
            logger.debug(f"sp_Blitz execution failed: {e}")
            return []
    
    async def _run_custom_analysis(
        self,
        mcp_client: IMCPDBClient,
        db_type: DatabaseType,
        connection_string: Optional[str],
        connection_name: Optional[str],
        connection_id: Optional[str],
        tenant_id: Optional[str]
    ) -> list:
        """Run custom DBA analysis"""
        custom_results = []
        
        # Run multiple checks
        checks = [
            ("slow_queries", "SELECT TOP 20 * FROM sys.dm_exec_query_stats ORDER BY total_elapsed_time DESC"),
            ("missing_indexes", "SELECT * FROM sys.dm_db_missing_index_details LIMIT 20"),
            ("fragmentation", "SELECT * FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED')"),
        ]
        
        for check_name, check_query in checks:
            try:
                result = await mcp_client.execute_query(
                    db_type=db_type,
                    query=check_query,
                    connection_string=connection_string
                )
                
                if result:
                    custom_results.append({
                        "check_name": check_name,
                        "finding_count": len(result) if isinstance(result, list) else 1,
                        "source": "custom_analysis",
                    })
            except Exception as e:
                logger.debug(f"Custom check {check_name} failed: {e}")
        
        return custom_results
    
    @staticmethod
    def _compare_results(blitz_results: list, custom_results: list) -> dict:
        """Compare sp_Blitz and custom analysis results"""
        blitz_findings = set()
        for result in blitz_results:
            blitz_findings.add(result.get("finding", "").lower())
        
        custom_findings = set()
        for result in custom_results:
            custom_findings.add(result.get("check_name", "").lower())
        
        common_findings = blitz_findings.intersection(custom_findings)
        
        return {
            "blitz_count": len(blitz_results),
            "custom_count": len(custom_results),
            "common_count": len(common_findings),
            "blitz_only": list(blitz_findings - custom_findings),
            "custom_only": list(custom_findings - blitz_findings),
            "common_findings": list(common_findings),
        }
