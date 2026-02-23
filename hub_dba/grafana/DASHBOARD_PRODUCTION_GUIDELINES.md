# DASHBOARD LAYOUT CHUẨN CHO DBA PRODUCTION
# Best practices: phân tách rõ scope, tránh aggregation sai, dùng rate() cho cumulative metrics

## 1. OVERVIEW DASHBOARD (Entry point)

### Panel 1: Health Score Table
**Query:**
```promql
# Health score per instance - weighted scoring
(
  # Connection overload (>500 concurrent = warning)
  (max by(instance, environment, hostname) (mssql_connections) > bool 500) * 2
  
  # Deadlock rate (>0.1 deadlock/sec = critical)
  + (rate(mssql_deadlocks_total[5m]) > bool 0.1) * 3
  
  # Blocking sessions (>10 blocked = warning)
  + (mssql_blocking_session_count > bool 10) * 2
  
  # SQL Agent down (critical)
  + (mssql_agent_status == bool 0) * 5
  
  # Long running queries (>5 queries >30s = warning)
  + (mssql_long_running_queries > bool 5) * 2
  
  # Low PLE (<300s = memory pressure)
  + (mssql_page_life_expectancy_seconds < bool 300) * 2
  
  # Backup stale (any DB with backup_status != 1)
  + (count by(instance) (mssql_backup_status != 1) > bool 0) * 1
  
  # DB offline (any DB with state != 0)
  + (count by(instance) (mssql_database_state != 0) > bool 0) * 3
)
```

**Visualization:** Table
- Columns: instance, environment, hostname, score
- Sort: score DESC (worst first)
- Thresholds:
  - 0-2: Healthy (green)
  - 3-6: Warning (yellow)
  - 7+: Critical (red)

**Drilldown:** Click instance → Instance Detail dashboard

---

### Panel 2: Active Alerts
**Query:**
```promql
ALERTS{alertstate="firing", job=~"sql-exporter.*"}
```

**Visualization:** Table
- Columns: alertname, instance, severity, summary
- Sort: severity (critical first)

---

### Panel 3: Capacity Forecast
**Query:**
```promql
# Database size growth rate (GB/day) - predict when disk full
predict_linear(mssql_database_size_gb{size_type="total_size_gb"}[30d], 86400 * 30)
```

**Visualization:** Bar gauge
- Thresholds: >80% disk capacity = red

---

## 2. INSTANCE DETAIL DASHBOARD

**Variables:**
- `$instance`: Instance IP:port
- `$environment`: dev/staging/prod

### Row 1: Performance Overview

#### Panel 2.1: Batch Requests/sec
**Query:**
```promql
rate(mssql_batch_requests_total{instance="$instance"}[1m])
```
**Viz:** Time series, unit: ops/s

#### Panel 2.2: Deadlocks/sec
**Query:**
```promql
rate(mssql_deadlocks_total{instance="$instance"}[5m])
```
**Viz:** Time series, threshold >0.1 = red

#### Panel 2.3: Buffer Cache Hit Ratio
**Query:**
```promql
mssql_buffer_cache_hit_ratio{instance="$instance"}
```
**Viz:** Gauge, threshold <90% = yellow, <80% = red

#### Panel 2.4: Page Life Expectancy
**Query:**
```promql
mssql_page_life_expectancy_seconds{instance="$instance"}
```
**Viz:** Time series, threshold <300s = red

---

### Row 2: Locks & Blocking

#### Panel 2.5: Blocking Sessions
**Query:**
```promql
mssql_blocking_session_count{instance="$instance"}
```
**Viz:** Time series, threshold >5 = yellow, >20 = red

**Drilldown:** Click → Blocking Detail panel (hidden row)

#### Panel 2.6: Lock Waits/sec
**Query:**
```promql
rate(mssql_lock_waits_total{instance="$instance"}[1m])
```
**Viz:** Time series

#### Panel 2.7: Lock Timeouts/sec
**Query:**
```promql
rate(mssql_lock_timeouts_total{instance="$instance"}[1m])
```
**Viz:** Time series

---

### Row 2B: Blocking Detail (collapsed by default)

#### Panel 2.8: Blocking Chain
**Query:**
```promql
mssql_blocking_detail_wait_ms{instance="$instance"} > 0
```
**Viz:** Table
- Columns: blocked_spid, blocking_spid, db_name, wait_type, wait_time_ms
- Sort: wait_time_ms DESC

**NOTE:** High cardinality. Chỉ hiển thị khi có blocking.

---

### Row 3: Memory

#### Panel 2.9: SQL Server Memory
**Query:**
```promql
# Resident vs Virtual memory
mssql_resident_memory_gb{instance="$instance"}
mssql_virtual_memory_gb{instance="$instance"}
```
**Viz:** Time series (2 lines)

#### Panel 2.10: OS Memory %
**Query:**
```promql
(mssql_os_memory{instance="$instance", state="used"} 
 / mssql_os_memory_total_gb{instance="$instance"}) * 100
```
**Viz:** Gauge, threshold >90% = red

---

### Row 4: Database Health

#### Panel 2.11: Database State
**Query:**
```promql
mssql_database_state{instance="$instance"}
```
**Viz:** Bar chart
- X-axis: db_name
- Y-axis: state (with value mappings: 0=Online, 6=Offline, etc.)
- Color: green if 0, red otherwise

#### Panel 2.12: Backup Status
**Query:**
```promql
mssql_backup_status{instance="$instance"}
```
**Viz:** Bar chart
- X-axis: db_name
- Y-axis: backup_status (1=Healthy, 0=Warning, -1=Critical)
- Color: green/yellow/red

**Drilldown:** Click DB → Database Detail dashboard

#### Panel 2.13: Database Size
**Query:**
```promql
mssql_database_size_gb{instance="$instance", size_type="total_size_gb"}
```
**Viz:** Bar chart, unit: GB

---

### Row 5: Wait Stats (từ advanced collector)

#### Panel 2.14: Top 10 Wait Types
**Query:**
```promql
topk(10, 
  rate(mssql_wait_stats_ms{instance="$instance"}[5m])
)
```
**Viz:** Bar chart
- X-axis: wait_type
- Y-axis: wait_time_ms/sec

---

## 3. DATABASE DETAIL DASHBOARD

**Variables:**
- `$instance`
- `$environment`
- `$database`: database name

### Row 1: Top Queries

#### Panel 3.1: Top 10 CPU Queries
**Query:**
```promql
topk(10, 
  mssql_top_cpu_queries_ms{instance="$instance", db_name="$database"}
)
```
**Viz:** Table
- Columns: query_hash, total_worker_time_ms, execution_count, avg_worker_time_ms
- Sort: avg_worker_time_ms DESC

**Drilldown:** query_hash → link to query text viewer (custom exporter endpoint)

#### Panel 3.2: Top 10 IO Queries
**Query:**
```promql
topk(10, 
  mssql_top_io_queries_reads{instance="$instance", db_name="$database"}
)
```
**Viz:** Table

---

### Row 2: Index Health

#### Panel 3.3: Fragmented Indexes
**Query:**
```promql
mssql_index_fragmentation_percent{instance="$instance", db_name="$database"} > 30
```
**Viz:** Table
- Columns: schema_name, table_name, index_name, avg_fragmentation_percent, page_count
- Sort: avg_fragmentation_percent DESC

**Alert:** fragmentation >70% + page_count >10000 → recommend rebuild

---

### Row 3: File IO

#### Panel 3.4: File IO Latency
**Query:**
```promql
mssql_file_io_stall_ms{instance="$instance", db_name="$database"}
```
**Viz:** Table
- Columns: file_logical_name, file_type, io_stall_read_ms, io_stall_write_ms
- Calc derived column: avg_read_latency = io_stall_read_ms / num_of_reads
- Threshold: >20ms = warning, >50ms = critical

---

### Row 4: Transaction Log

#### Panel 3.5: Log Space Used %
**Query:**
```promql
mssql_log_space_used_percent{instance="$instance", db_name="$database"}
```
**Viz:** Gauge, threshold >80% = red

**Alert rule:**
```promql
mssql_log_space_used_percent > 90
```

---

## 4. ALERT RULES (Prometheus)

```yaml
groups:
  - name: sql_server_alerts
    interval: 30s
    rules:
      # Critical: SQL Agent down
      - alert: SQLAgentDown
        expr: mssql_agent_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "SQL Server Agent down on {{ $labels.instance }}"
          description: "Agent has been down for >2 minutes."

      # Critical: Deadlock storm
      - alert: DeadlockStorm
        expr: rate(mssql_deadlocks_total[5m]) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Deadlock storm on {{ $labels.instance }}"
          description: "{{ $value }} deadlocks/sec for >5 minutes."

      # Warning: Memory pressure
      - alert: LowPageLifeExpectancy
        expr: mssql_page_life_expectancy_seconds < 300
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Memory pressure on {{ $labels.instance }}"
          description: "PLE = {{ $value }}s (<300s threshold)."

      # Critical: Database offline
      - alert: DatabaseOffline
        expr: mssql_database_state == 6
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database {{ $labels.db }} offline on {{ $labels.instance }}"

      # Warning: Backup stale
      - alert: BackupStale
        expr: mssql_backup_status{backup_type="Full"} != 1
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Backup stale for {{ $labels.db }} on {{ $labels.instance }}"
          description: "Last full backup >24h ago."

      # Critical: Transaction log full
      - alert: TransactionLogFull
        expr: mssql_log_space_used_percent > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Transaction log full on {{ $labels.db_name }}"
          description: "Log space {{ $value }}% used."

      # Warning: Blocking sessions
      - alert: HighBlockingCount
        expr: mssql_blocking_session_count > 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High blocking on {{ $labels.instance }}"
          description: "{{ $value }} sessions blocked for >5 minutes."
```

---

## 5. DASHBOARD ARCHITECTURE PRINCIPLES

1. **Scope separation:**
   - Overview: cross-instance comparison
   - Instance Detail: single instance, all metrics
   - Database Detail: single DB, deep dive

2. **Avoid aggregation errors:**
   - NEVER `sum(mssql_database_state)` → meaningless
   - Use `count(...!= 0)` for boolean aggregation
   - Use `rate()` for cumulative counters, not raw value

3. **Threshold design:**
   - Based on production baseline, not arbitrary
   - Page Life Expectancy: 300s = rule of thumb for <16GB RAM, scale up for larger
   - Deadlocks: >0.1/sec = investigate, >1/sec = critical

4. **Cardinality management:**
   - Per-DB metrics: only for critical DBs, or aggregate small DBs
   - Per-query metrics (query_hash): limit to TOP 10, scrape interval 60s
   - Per-SPID metrics (blocking detail): ephemeral, drop after 5 min

5. **Performance:**
   - Standard collector: 15s scrape
   - Advanced collector: 60s scrape
   - Size/fragmentation: 1h scrape (separate job)

---

## 6. RECOMMENDED GRAFANA PLUGIN

- **Pie Chart**: for database size distribution
- **State Timeline**: for database state history (online/offline events)
- **Heatmap**: for wait type distribution over time
- **Table**: with **data links** to SSMS or query text viewer

---

## 7. PROMETHEUS RECORDING RULES (optimization)

```yaml
groups:
  - name: sql_server_recording_rules
    interval: 15s
    rules:
      # Pre-compute rate to reduce dashboard query load
      - record: mssql:batch_requests:rate1m
        expr: rate(mssql_batch_requests_total[1m])

      - record: mssql:deadlocks:rate5m
        expr: rate(mssql_deadlocks_total[5m])

      - record: mssql:lock_waits:rate1m
        expr: rate(mssql_lock_waits_total[1m])

      # Aggregate per-database connections to instance level (for overview)
      - record: mssql:connections:instance_total
        expr: sum by(instance, environment, hostname) (mssql_connections)

      # Health score pre-computation
      - record: mssql:health_score:instance
        expr: |
          (
            (mssql:connections:instance_total > bool 500) * 2
            + (mssql:deadlocks:rate5m > bool 0.1) * 3
            + (mssql_blocking_session_count > bool 10) * 2
            + (mssql_agent_status == bool 0) * 5
            + (mssql_long_running_queries > bool 5) * 2
            + (mssql_page_life_expectancy_seconds < bool 300) * 2
            + (count by(instance) (mssql_backup_status != 1) > bool 0) * 1
            + (count by(instance) (mssql_database_state != 0) > bool 0) * 3
          )
```

Dashboard query trở thành:
```promql
mssql:health_score:instance
```
→ Faster, less Prometheus load.

---

## 8. CHEAT SHEET - COMMON PROMQL PATTERNS

| Need | PromQL Pattern | Example |
|------|----------------|---------|
| Rate of counter | `rate(metric_total[5m])` | `rate(mssql_deadlocks_total[5m])` |
| Delta of counter | `increase(metric_total[5m])` | `increase(mssql_batch_requests_total[5m])` |
| Count non-zero | `count(...!= 0)` | `count(mssql_database_state != 0)` |
| Top N | `topk(N, metric)` | `topk(10, mssql_connections)` |
| Per-database to instance | `sum by(instance)` | `sum by(instance)(mssql_connections)` |
| Memory % | `(used / total) * 100` | `(mssql_os_memory{state="used"}/mssql_os_memory_total_gb)*100` |
| Predict growth | `predict_linear(metric[30d], seconds)` | `predict_linear(mssql_database_size_gb[30d], 86400*30)` |
