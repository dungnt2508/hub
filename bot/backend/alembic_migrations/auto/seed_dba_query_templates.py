"""
Seed DBA Query Templates Data
Migrate queries from execution_plan_generator.py and mcp_server/query_templates.py into database

Usage:
    python -m backend.alembic_migrations.auto.seed_dba_query_templates
"""
import asyncio
import sys
import os
from uuid import UUID

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.infrastructure.database_client import database_client
from backend.infrastructure.dba_query_template_repository import dba_query_template_repository
from backend.shared.logger import logger


# Queries from execution_plan_generator.py
QUERY_TEMPLATES = {
    "QUERY_PERFORMANCE": {
        "sqlserver": [
            {
                "step_number": 1,
                "purpose": "Get top slow queries",
                "query_text": """
                    EXEC sp_BlitzCache @SortOrder = 'duration';
                """,
                "read_only": True,
            },
            {
                "step_number": 2,
                "purpose": "Get execution plan for slowest query",
                "query_text": """
                    SELECT TOP 1
                        qp.query_plan
                    FROM sys.dm_exec_query_stats qs
                    CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
                    ORDER BY qs.total_elapsed_time DESC
                """,
                "read_only": True,
            },
            {
                "step_number": 3,
                "purpose": "Get missing indexes",
                "query_text": """
                    SELECT TOP 20
                        migs.avg_total_user_cost,
                        migs.avg_user_impact,
                        migs.user_seeks,
                        migs.user_scans,
                        mid.equality_columns,
                        mid.inequality_columns,
                        mid.included_columns,
                        mid.statement as table_name
                    FROM sys.dm_db_missing_index_groups mig
                    INNER JOIN sys.dm_db_missing_index_group_stats migs ON mig.group_id = migs.group_id
                    INNER JOIN sys.dm_db_missing_index_details mid ON mig.index_handle = mid.index_handle
                    ORDER BY migs.avg_user_impact * migs.user_seeks DESC
                """,
                "read_only": True,
            },
        ],
        "postgresql": [
            {
                "step_number": 1,
                "purpose": "Get top slow queries",
                "query_text": """
                    SELECT 
                        query,
                        calls,
                        total_exec_time,
                        mean_exec_time,
                        max_exec_time,
                        min_exec_time,
                        rows
                    FROM pg_stat_statements
                    ORDER BY mean_exec_time DESC
                    LIMIT 10
                """,
                "read_only": True,
            },
            {
                "step_number": 2,
                "purpose": "Get query plans",
                "query_text": """
                    SELECT
                        query,
                        calls,
                        total_exec_time
                    FROM pg_stat_statements
                    ORDER BY total_exec_time DESC
                    LIMIT 5
                """,
                "read_only": True,
            },
        ],
    },
    "INDEX_HEALTH": {
        "sqlserver": [
            {
                "step_number": 1,
                "purpose": "Get fragmented indexes",
                "query_text": """
                    SELECT TOP 20
                        OBJECT_NAME(ips.object_id) as table_name,
                        i.name as index_name,
                        ips.index_type_desc,
                        ips.avg_fragmentation_in_percent,
                        ips.page_count
                    FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
                    INNER JOIN sys.indexes i ON ips.object_id = i.object_id
                        AND ips.index_id = i.index_id
                    WHERE ips.avg_fragmentation_in_percent > 10
                    ORDER BY ips.avg_fragmentation_in_percent DESC
                """,
                "read_only": True,
            },
            {
                "step_number": 2,
                "purpose": "Get unused indexes",
                "query_text": """
                    SELECT TOP 20
                        OBJECT_NAME(i.object_id) as table_name,
                        i.name as index_name,
                        ISNULL(s.user_updates, 0) as user_updates,
                        ISNULL(s.user_seeks, 0) as user_seeks,
                        ISNULL(s.user_scans, 0) as user_scans,
                        ISNULL(s.user_lookups, 0) as user_lookups
                    FROM sys.indexes i
                    LEFT JOIN sys.dm_db_index_usage_stats s ON i.object_id = s.object_id
                        AND i.index_id = s.index_id
                    WHERE OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
                        AND i.index_id > 0
                        AND (ISNULL(s.user_seeks, 0) + ISNULL(s.user_scans, 0) + ISNULL(s.user_lookups, 0) = 0)
                    ORDER BY OBJECT_NAME(i.object_id), i.name
                """,
                "read_only": True,
            },
        ],
    },
    "BLOCKING_ANALYSIS": {
        "sqlserver": [
            {
                "step_number": 1,
                "purpose": "Get current blocking sessions",
                "query_text": """
                    SELECT
                        er.session_id,
                        er.status,
                        er.wait_type,
                        er.wait_time_ms,
                        er.blocking_session_id,
                        t.text as last_query
                    FROM sys.dm_exec_requests er
                    CROSS APPLY sys.dm_exec_sql_text(er.sql_handle) t
                    WHERE er.blocking_session_id > 0
                """,
                "read_only": True,
            },
            {
                "step_number": 2,
                "purpose": "Get lock information",
                "query_text": """
                    SELECT
                        resource_type,
                        request_mode,
                        request_status,
                        COUNT(*) as count
                    FROM sys.dm_tran_locks
                    GROUP BY resource_type, request_mode, request_status
                """,
                "read_only": True,
            },
        ],
    },
    "WAIT_STATISTICS": {
        "sqlserver": [
            {
                "step_number": 1,
                "purpose": "Get top wait statistics",
                "query_text": """
                    SELECT TOP 20
                        wait_type,
                        wait_time_ms,
                        signal_wait_time_ms,
                        waiting_tasks_count,
                        100.0 * wait_time_ms / SUM(wait_time_ms) OVER() as percentage
                    FROM sys.dm_os_wait_stats
                    WHERE wait_type NOT IN (
                        'SLEEP_TASK', 'LAZYWRITER_SLEEP', 'SQLTRACE_BUFFER_FLUSH',
                        'CLR_SEMAPHORE', 'CLR_AUTO_EVENT'
                    )
                    ORDER BY wait_time_ms DESC
                """,
                "read_only": True,
            },
        ],
    },
    "DEADLOCK_DETECTION": {
        "sqlserver": [
            {
                "step_number": 1,
                "purpose": "Get deadlock graph",
                "query_text": """
                    SELECT
                        database_id,
                        name
                    FROM sys.databases
                    WHERE is_read_only = 0
                """,
                "read_only": True,
            },
        ],
    },
    "IO_PRESSURE": {
        "sqlserver": [
            {
                "step_number": 1,
                "purpose": "Get I/O statistics",
                "query_text": """
                    SELECT TOP 20
                        OBJECT_NAME(ips.object_id) as table_name,
                        i.name as index_name,
                        ips.page_io_latch_wait_count,
                        ips.page_io_latch_wait_in_ms,
                        ips.tree_page_latch_wait_count,
                        ips.tree_page_latch_wait_in_ms
                    FROM sys.dm_db_index_operational_stats(DB_ID(), NULL, NULL, NULL) ips
                    INNER JOIN sys.indexes i ON ips.object_id = i.object_id
                        AND ips.index_id = i.index_id
                    WHERE ips.page_io_latch_wait_count > 0
                    ORDER BY ips.page_io_latch_wait_in_ms DESC
                """,
                "read_only": True,
            },
        ],
    },
    "CAPACITY_PLANNING": {
        "sqlserver": [
            {
                "step_number": 1,
                "purpose": "Get database size",
                "query_text": """
                    SELECT
                        name as database_name,
                        CAST(SUM(size) * 8 / 1024 AS DECIMAL(10,2)) as size_mb
                    FROM sys.master_files
                    WHERE database_id = DB_ID()
                    GROUP BY name
                """,
                "read_only": True,
            },
        ],
    },
}


async def seed_dba_query_templates():
    """Seed DBA query templates from code into database"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database for seeding DBA query templates")
        
        stats = {
            "created": 0,
            "skipped": 0,
            "errors": 0,
        }
        
        # Insert queries for each playbook
        for playbook_name, db_types in QUERY_TEMPLATES.items():
            for db_type, steps in db_types.items():
                for step in steps:
                    try:
                        # Check if template already exists
                        existing = await dba_query_template_repository.get_templates_by_playbook(
                            playbook_name=playbook_name,
                            db_type=db_type,
                            active_only=False
                        )
                        
                        # Check if this step already exists
                        step_exists = any(
                            t['step_number'] == step['step_number'] and t['query_text'].strip() == step['query_text'].strip()
                            for t in existing
                        )
                        
                        if step_exists:
                            logger.debug(f"Template already exists: {playbook_name}/{db_type}/step_{step['step_number']}")
                            stats["skipped"] += 1
                            continue
                        
                        # Create template
                        await dba_query_template_repository.create_template(
                            playbook_name=playbook_name,
                            db_type=db_type,
                            step_number=step['step_number'],
                            purpose=step['purpose'],
                            query_text=step['query_text'].strip(),
                            read_only=step.get('read_only', True),
                            description=f"Query template for {playbook_name} playbook, step {step['step_number']}",
                            created_by=None,  # System migration
                        )
                        
                        stats["created"] += 1
                        logger.debug(f"Created template: {playbook_name}/{db_type}/step_{step['step_number']}")
                        
                    except Exception as e:
                        logger.error(
                            f"Error creating template {playbook_name}/{db_type}/step_{step['step_number']}: {e}",
                            exc_info=True
                        )
                        stats["errors"] += 1
        
        logger.info(f"✅ Successfully seeded DBA query templates: {stats}")
        print(f"\n✅ Đã migrate DBA query templates thành công!")
        print(f"   - Created: {stats['created']}")
        print(f"   - Skipped: {stats['skipped']}")
        print(f"   - Errors: {stats['errors']}")
        
    except Exception as e:
        logger.error(f"Error seeding DBA query templates: {e}", exc_info=True)
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        await database_client.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_dba_query_templates())

