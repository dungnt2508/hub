"""
Query Templates for DBA Domain
Provides database-specific query templates for various DBA analysis tasks
"""

from .ports.mcp_client import DatabaseType
from typing import Dict, Optional


class QueryTemplates:
    """Query templates for different database types and analysis tasks"""
    
    # PostgreSQL Templates
    POSTGRESQL_TEMPLATES = {
        "slow_queries": """
            SELECT 
                query,
                calls,
                total_exec_time as total_time_ms,
                mean_exec_time as mean_time_ms,
                max_exec_time as max_time_ms,
                min_exec_time as min_time_ms,
                rows
            FROM pg_stat_statements
            WHERE mean_exec_time > :min_duration_ms
            ORDER BY mean_exec_time DESC
            LIMIT :limit
        """,
        "index_health": """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as index_tuples_read,
                idx_tup_fetch as index_tuples_fetched
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
        """,
        "blocking": """
            SELECT 
                blocking_locks.pid as blocking_pid,
                blocked_locks.pid as blocked_pid,
                blocked_locks.relation::regclass as table_name,
                blocked_locks.mode as lock_mode
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_locks blocking_locks 
                ON blocking_locks.locktype = blocked_locks.locktype
                AND blocking_locks.database = blocked_locks.database
                AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                AND blocking_locks.pid != blocked_locks.pid
            WHERE NOT blocked_locks.granted
        """,
        "wait_stats": """
            SELECT 
                event as wait_event,
                count as wait_count,
                total_time_ms,
                mean_time_ms,
                max_time_ms
            FROM pg_stat_statements_info
            ORDER BY total_time_ms DESC
        """,
        "database_size": """
            SELECT 
                datname as database_name,
                pg_database_size(datname) as size_bytes
            FROM pg_database
            WHERE datname NOT IN ('postgres', 'template0', 'template1')
        """,
    }
    
    # MySQL Templates
    MYSQL_TEMPLATES = {
        "slow_queries": """
            SELECT 
                digest_text as query,
                COUNT_STAR as calls,
                SUM_TIMER_WAIT / 1000000000000 as total_time_ms,
                AVG_TIMER_WAIT / 1000000000000 as mean_time_ms,
                MAX_TIMER_WAIT / 1000000000000 as max_time_ms,
                MIN_TIMER_WAIT / 1000000000000 as min_time_ms,
                SUM_ROWS_EXAMINED as rows_examined
            FROM performance_schema.events_statements_summary_by_digest
            WHERE AVG_TIMER_WAIT / 1000000000000 > :min_duration_ms
            ORDER BY SUM_TIMER_WAIT DESC
            LIMIT :limit
        """,
        "index_health": """
            SELECT 
                OBJECT_SCHEMA as schema_name,
                OBJECT_NAME as table_name,
                INDEX_NAME as index_name,
                COUNT_READ as index_scans,
                COUNT_INSERT as insert_count,
                COUNT_UPDATE as update_count,
                COUNT_DELETE as delete_count
            FROM performance_schema.table_io_waits_summary_by_index_usage
            ORDER BY COUNT_READ DESC
        """,
        "blocking": """
            SELECT 
                waiting_trx_id as blocked_session_id,
                waiting_pid as blocked_pid,
                waiting_query as blocked_query,
                blocking_trx_id as blocking_session_id,
                blocking_pid as blocking_pid,
                blocking_query as blocking_query,
                wait_age_secs as blocked_duration_ms
            FROM sys.innodb_trx t1
            INNER JOIN sys.innodb_trx t2 
                WHERE t1.trx_wait_started IS NOT NULL
                AND t1.trx_isolation_level != 'SERIALIZABLE'
        """,
        "wait_stats": """
            SELECT 
                EVENT_NAME as wait_event,
                COUNT_STAR as wait_count,
                SUM_TIMER_WAIT / 1000000000000 as total_wait_time_ms,
                AVG_TIMER_WAIT / 1000000000000 as avg_wait_time_ms,
                MAX_TIMER_WAIT / 1000000000000 as max_wait_time_ms
            FROM performance_schema.events_waits_summary_global_by_event_name
            WHERE SUM_TIMER_WAIT > 0
            ORDER BY SUM_TIMER_WAIT DESC
        """,
        "database_size": """
            SELECT 
                table_schema as database_name,
                SUM(data_length + index_length) as size_bytes,
                COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            GROUP BY table_schema
        """,
    }
    
    # SQL Server Templates
    SQLSERVER_TEMPLATES = {
        "slow_queries": """
            SELECT TOP :limit
                text as query,
                execution_count as calls,
                total_elapsed_time / 1000 as total_time_ms,
                total_elapsed_time / execution_count / 1000 as mean_time_ms,
                max_elapsed_time / 1000 as max_time_ms,
                min_elapsed_time / 1000 as min_time_ms
            FROM sys.dm_exec_query_stats
            CROSS APPLY sys.dm_exec_sql_text(sql_handle)
            WHERE total_elapsed_time / execution_count / 1000 > :min_duration_ms
            ORDER BY total_elapsed_time DESC
        """,
        "index_health": """
            SELECT 
                OBJECT_NAME(i.object_id) as table_name,
                i.name as index_name,
                ps.user_seeks as index_scans,
                ps.user_updates,
                ps.avg_fragmentation_in_percent as fragmentation_percent
            FROM sys.indexes i
            LEFT JOIN sys.dm_db_index_usage_stats ps 
                ON i.object_id = ps.object_id 
                AND i.index_id = ps.index_id
            LEFT JOIN sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
                ON i.object_id = ips.object_id 
                AND i.index_id = ips.index_id
            ORDER BY ps.user_seeks DESC
        """,
        "blocking": """
            SELECT 
                waiting_task_address as blocked_session_id,
                session_id as blocking_pid,
                (SELECT text FROM sys.dm_exec_sql_text(sql_handle)) as blocking_query
            FROM sys.dm_exec_requests
            WHERE blocking_session_id != 0
        """,
        "wait_stats": """
            SELECT TOP 20
                wait_type,
                waiting_tasks_count as wait_count,
                wait_time_ms as total_wait_time_ms,
                wait_time_ms / waiting_tasks_count as avg_wait_time_ms,
                max_wait_time_ms
            FROM sys.dm_os_wait_stats
            WHERE wait_type NOT IN (
                'CLR_SEMAPHORE', 'DBMIRROR_DBM_EVENT', 'DBMIRROR_EVENTS_QUEUE',
                'DBMIRROR_WORKER_QUEUE', 'DIRTY_PAGE_POLL', 'DISPATCHER_QUEUE_SEMAPHORE',
                'SLEEP_TASK', 'SLEEP_SYSTEMTASK'
            )
            ORDER BY wait_time_ms DESC
        """,
        "database_size": """
            SELECT 
                name as database_name,
                (size * 8) / 1024.0 as size_mb
            FROM sys.master_files
            WHERE database_id > 4
            GROUP BY name, size
        """,
    }
    
    @classmethod
    def get_template(cls, db_type: DatabaseType, query_type: str) -> Optional[str]:
        """
        Get query template for specific database type and query type.
        
        Args:
            db_type: Database type
            query_type: Type of query (e.g., 'slow_queries', 'index_health', etc.)
            
        Returns:
            Query template string or None if not found
        """
        if db_type == DatabaseType.POSTGRESQL:
            return cls.POSTGRESQL_TEMPLATES.get(query_type)
        elif db_type == DatabaseType.MYSQL:
            return cls.MYSQL_TEMPLATES.get(query_type)
        elif db_type == DatabaseType.SQLSERVER:
            return cls.SQLSERVER_TEMPLATES.get(query_type)
        else:
            return None
    
    @classmethod
    def get_all_templates(cls, db_type: DatabaseType) -> Dict[str, str]:
        """
        Get all templates for a specific database type.
        
        Args:
            db_type: Database type
            
        Returns:
            Dictionary of templates for the database type
        """
        if db_type == DatabaseType.POSTGRESQL:
            return cls.POSTGRESQL_TEMPLATES.copy()
        elif db_type == DatabaseType.MYSQL:
            return cls.MYSQL_TEMPLATES.copy()
        elif db_type == DatabaseType.SQLSERVER:
            return cls.SQLSERVER_TEMPLATES.copy()
        else:
            return {}
