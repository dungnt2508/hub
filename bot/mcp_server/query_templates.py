"""
Query Templates for Different Database Types
"""
from .database_adapters import DatabaseType

QUERY_TEMPLATES = {
    DatabaseType.POSTGRESQL: {
        "slow_queries": """
            SELECT 
                query,
                calls,
                total_exec_time as total_time_ms,
                mean_exec_time as mean_time_ms,
                max_exec_time as max_time_ms,
                min_exec_time as min_time_ms,
                rows as rows_returned
            FROM pg_stat_statements
            WHERE mean_exec_time > %(min_duration_ms)s
            ORDER BY mean_exec_time DESC
            LIMIT %(limit)s
        """,
        "wait_stats": """
            SELECT 
                wait_event_type,
                wait_event,
                count(*) as wait_count
            FROM pg_stat_activity
            WHERE wait_event IS NOT NULL
            GROUP BY wait_event_type, wait_event
            ORDER BY wait_count DESC
        """,
        "index_health": """
            SELECT 
                schemaname as schema_name,
                tablename as table_name,
                indexname as index_name,
                idx_scan as index_scans,
                idx_tup_read as index_tuples_read,
                idx_tup_fetch as index_tuples_fetched
            FROM pg_stat_user_indexes
            WHERE schemaname = COALESCE(%(schema)s, schemaname)
            ORDER BY idx_scan ASC
        """,
        "blocking": """
            SELECT 
                blocked_locks.pid AS blocked_pid,
                blocking_locks.pid AS blocking_pid,
                blocked_activity.query AS blocked_query,
                blocking_activity.query AS blocking_query,
                blocked_activity.wait_event_type,
                blocked_activity.wait_event
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_stat_activity blocked_activity 
                ON blocked_activity.pid = blocked_locks.pid
            JOIN pg_catalog.pg_locks blocking_locks 
                ON blocking_locks.locktype = blocked_locks.locktype
                AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                AND blocking_locks.pid != blocked_locks.pid
            JOIN pg_catalog.pg_stat_activity blocking_activity 
                ON blocking_activity.pid = blocking_locks.pid
            WHERE NOT blocked_locks.granted
        """,
    },
    DatabaseType.MYSQL: {
        "slow_queries": """
            SELECT 
                sql_text as query,
                exec_count as calls,
                avg_timer_wait / 1000000000000 as mean_time_ms,
                max_timer_wait / 1000000000000 as max_time_ms,
                sum_timer_wait / 1000000000000 as total_time_ms
            FROM performance_schema.events_statements_summary_by_digest
            WHERE avg_timer_wait > %(min_duration_ms)s * 1000000000
            ORDER BY avg_timer_wait DESC
            LIMIT %(limit)s
        """,
        "wait_stats": """
            SELECT 
                event_name as wait_event,
                count_star as wait_count,
                sum_timer_wait / 1000000000000 as total_wait_time_ms,
                avg_timer_wait / 1000000000000 as avg_wait_time_ms
            FROM performance_schema.events_waits_summary_global_by_event_name
            WHERE event_name NOT LIKE 'idle%'
            ORDER BY sum_timer_wait DESC
        """,
        "index_health": """
            SELECT 
                table_schema as schema_name,
                table_name,
                index_name,
                seq_in_index,
                cardinality
            FROM information_schema.statistics
            WHERE table_schema = COALESCE(%(schema)s, table_schema)
            ORDER BY table_schema, table_name, index_name
        """,
        "blocking": """
            SELECT 
                r.trx_id waiting_trx_id,
                r.trx_mysql_thread_id waiting_thread,
                r.trx_query waiting_query,
                b.trx_id blocking_trx_id,
                b.trx_mysql_thread_id blocking_thread,
                b.trx_query blocking_query
            FROM information_schema.innodb_lock_waits w
            INNER JOIN information_schema.innodb_trx b 
                ON b.trx_id = w.blocking_trx_id
            INNER JOIN information_schema.innodb_trx r 
                ON r.trx_id = w.requesting_trx_id
        """,
    },
    DatabaseType.SQLSERVER: {
        "slow_queries": """
            SELECT TOP %(limit)s
                query_stats.execution_count as calls,
                query_stats.total_elapsed_time / 1000000.0 as total_time_ms,
                query_stats.avg_elapsed_time / 1000000.0 as mean_time_ms,
                query_stats.max_elapsed_time / 1000000.0 as max_time_ms,
                sql_text.text as query
            FROM sys.dm_exec_query_stats query_stats
            CROSS APPLY sys.dm_exec_sql_text(query_stats.sql_handle) AS sql_text
            WHERE query_stats.avg_elapsed_time / 1000000.0 > %(min_duration_ms)s
            ORDER BY query_stats.avg_elapsed_time DESC
        """,
        "wait_stats": """
            SELECT 
                wait_type as wait_event,
                waiting_tasks_count as wait_count,
                wait_time_ms as total_wait_time_ms,
                max_wait_time_ms,
                signal_wait_time_ms
            FROM sys.dm_os_wait_stats
            WHERE wait_type NOT LIKE 'SQLCLR%'
                AND wait_type NOT LIKE 'XACT%'
            ORDER BY wait_time_ms DESC
        """,
        "index_health": """
            SELECT 
                OBJECT_SCHEMA_NAME(i.object_id) as schema_name,
                OBJECT_NAME(i.object_id) as table_name,
                i.name as index_name,
                s.user_seeks,
                s.user_scans,
                s.user_lookups,
                s.user_updates
            FROM sys.indexes i
            LEFT JOIN sys.dm_db_index_usage_stats s 
                ON s.object_id = i.object_id 
                AND s.index_id = i.index_id
            WHERE i.object_id > 100
            ORDER BY s.user_seeks + s.user_scans + s.user_lookups ASC
        """,
        "blocking": """
            SELECT 
                r.session_id as blocked_session_id,
                r.blocking_session_id,
                r.wait_type,
                r.wait_time as blocked_duration_ms,
                r.command as blocked_command,
                s1.text as blocked_query,
                s2.text as blocking_query
            FROM sys.dm_exec_requests r
            CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) s1
            LEFT JOIN sys.dm_exec_requests r2 
                ON r2.session_id = r.blocking_session_id
            CROSS APPLY sys.dm_exec_sql_text(r2.sql_handle) s2
            WHERE r.blocking_session_id > 0
        """,
    },
}

