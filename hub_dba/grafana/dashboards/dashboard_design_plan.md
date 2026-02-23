# Dashboard Design Plan: SQL Server Instance Detail (Production)

## Objective
Thiết kế dashboard production-grade cho phép DBA **nhìn 1 phát biết ngay** hệ thống đang gặp vấn đề gì, covering đầy đủ 26 metrics từ `mssql_production.collector.yml`.

## Design Principles

### 1. **Top-Down Priority Layout**
```
┌─────────────────────────────────────────────┐
│  🚨 CRITICAL ALERTS (Red/Yellow Indicators) │ ← Nhìn đầu tiên
├─────────────────────────────────────────────┤
│  📊 KEY PERFORMANCE INDICATORS (KPIs)       │ ← Gauge/Stats
├─────────────────────────────────────────────┤
│  🧠 RESOURCE USAGE (Memory, CPU, IO)        │ ← Trends
├─────────────────────────────────────────────┤
│  🗄️ STORAGE & CAPACITY                      │ ← Planning
├─────────────────────────────────────────────┤
│  🔒 LOCKS & BLOCKING                        │ ← Concurrency
├─────────────────────────────────────────────┤
│  💿 DATABASE HEALTH                         │ ← State/Backup
├─────────────────────────────────────────────┤
│  🔍 ADVANCED DIAGNOSTICS                    │ ← Deep dive
└─────────────────────────────────────────────┘
```

### 2. **Color Coding Strategy**
- **Red**: Critical (Action required NOW)
- **Yellow**: Warning (Monitor closely)
- **Green**: Healthy
- **Blue**: Informational

### 3. **Metric Coverage**
All 26 metrics MUST be visualized or used in calculations.

---

## Proposed Dashboard Structure

### Row 1: 🚨 Critical Health Alerts (Height: 3 units)
**Purpose**: Instant visual alert if anything is critically wrong.

| Panel | Type | Metric | Threshold | Width |
|-------|------|--------|-----------|-------|
| Agent Status | Stat | `mssql_agent_status` | Red if 0 | 3 |
| Deadlocks/s | Stat | `rate(mssql_deadlocks_total)` | Red if > 0.1 | 3 |
| Blocking Sessions | Stat | `mssql_blocking_session_count` | Red if > 10 | 3 |
| Long Queries | Stat | `mssql_long_running_queries` | Red if > 5 | 3 |
| User Errors/s | Stat | `rate(mssql_user_errors_total)` | Red if > 10 | 3 |
| Log Space % | Gauge | `mssql_log_space_used_percent` | Red if > 85% | 3 |
| PLE (Memory) | Gauge | `mssql_page_life_expectancy_seconds` | Red if < 300s | 3 |
| Health Score | Stat | Calculated (existing formula) | Red if > 7 | 3 |

> **Rationale**: DBA glances tại row này → thấy RED là biết ngay phải check gì.

---

### Row 2: 📊 Key Performance Indicators (Height: 6 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| Uptime | Stat | `mssql_uptime_seconds` (format as days/hours) | 4 |
| Batch Requests/s | Time Series | `rate(mssql_batch_requests_total)` | 10 |
| Logins/s | Time Series | `rate(mssql_logins_total)` | 10 |

> **New additions**: `mssql_uptime_seconds`, `mssql_logins_total` (hiện đang thiếu).

---

### Row 3: 🧠 Memory & Buffer Pool (Height: 7 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| SQL Memory (GB) | Time Series | `mssql_memory_usage_gb` (resident + virtual) | 8 |
| Buffer Hit Ratio | Gauge | `mssql_buffer_cache_hit_ratio` | 4 |
| Page Life Expectancy | Time Series | `mssql_page_life_expectancy_seconds` | 6 |
| Lazy Writes/s | Time Series | `rate(mssql_lazy_writes_total)` | 6 |

> **New addition**: `mssql_lazy_writes_total` (memory pressure indicator).

---

### Row 4: 💽 OS Memory (Height: 6 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| OS Memory % | Gauge | Calculated from `mssql_os_memory` | 6 |
| OS Memory Breakdown | Pie Chart | `mssql_os_memory` (used/available) | 6 |
| OS Total Memory | Stat | `mssql_os_memory_total_gb` | 4 |
| SQL vs OS Memory | Time Series | Combined view | 8 |

---

### Row 5: 💾 Storage & I/O Performance (Height: 8 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| Read Latency (ms) | Time Series | `rate(mssql_io_stall_ms_total{io_type="read"}) / rate(num_of_reads)` | 6 |
| Write Latency (ms) | Time Series | `rate(mssql_io_stall_ms_total{io_type="write"}) / rate(num_of_writes)` | 6 |
| Log Space Used % | Time Series | `mssql_log_space_used_percent` (by DB) | 6 |
| Log Size (MB) | Bar Chart | `mssql_log_space_used_percent{stat="log_size_mb"}` | 6 |

> **New addition**: `mssql_io_stall_ms_total` (disk latency - CRITICAL cho production).

---

### Row 6: 🔒 Locks, Blocking & Deadlocks (Height: 7 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| Deadlocks/s | Time Series | `rate(mssql_deadlocks_total)` | 6 |
| Blocking Sessions | Time Series | `mssql_blocking_session_count` | 6 |
| Lock Waits/s | Time Series | `rate(mssql_lock_waits_total)` | 6 |
| Lock Timeouts/s | Time Series | `rate(mssql_lock_timeouts_total)` | 6 |

---

### Row 7: 🔌 Connections & Sessions (Height: 7 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| Connections by DB | Time Series (Stacked) | `mssql_connections` | 12 |
| Total Connections | Stat | `sum(mssql_connections)` | 4 |
| Long Queries (>30s) | Time Series | `mssql_long_running_queries` | 8 |

---

### Row 8: 💿 Database Health & Backup (Height: 8 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| Database State | Table | `mssql_database_state` | 8 |
| Backup Status | Table | `mssql_backup_status` | 8 |
| Database Size | Bar Chart | `mssql_database_size_gb` | 8 |

---

### Row 9: 🔍 Advanced Diagnostics (Height: 9 units)

| Panel | Type | Metric | Width |
|-------|------|--------|-------|
| Wait Stats (ms/s) | Time Series (Stacked) | `rate(mssql_wait_stats_ms_total)` | 12 |
| Blitz Findings | Table | `mssql_blitz_findings` | 6 |
| Top CPU Queries (Blitz) | Table | `mssql_blitz_cache_cpu_top10` | 6 |
| Blitz Snapshot Age | Stat | `mssql_blitz_snapshot_age_hours` | 6 |

> **New additions**: `mssql_blitz_cache_cpu_top10`, `mssql_blitz_snapshot_age_hours`.

---

## Metrics Coverage Checklist

| # | Metric | Dashboard Section | Panel Type |
|---|--------|-------------------|------------|
| 1 | `mssql_uptime_seconds` | KPIs | Stat | ✅ NEW |
| 2 | `mssql_batch_requests_total` | KPIs | Time Series | ✅ Existing |
| 3 | `mssql_user_errors_total` | Critical Alerts | Stat | ✅ NEW |
| 4 | `mssql_deadlocks_total` | Locks & Critical | Time Series + Stat | ✅ Existing |
| 5 | `mssql_logins_total` | KPIs | Time Series | ✅ NEW |
| 6 | `mssql_connections` | Connections | Time Series | ✅ Existing |
| 7 | `mssql_page_life_expectancy_seconds` | Memory + Critical | Time Series + Gauge | ✅ Existing |
| 8 | `mssql_memory_usage_gb` | Memory | Time Series | ✅ Existing |
| 9 | `mssql_lazy_writes_total` | Memory | Time Series | ✅ NEW |
| 10 | `mssql_wait_stats_ms_total` | Advanced Diagnostics | Time Series | ✅ Existing |
| 11 | `mssql_io_stall_ms_total` | Storage & IO | Time Series (Latency calc) | ✅ NEW |
| 12 | `mssql_log_space_used_percent` | Storage + Critical | Time Series + Gauge | ✅ NEW |
| 13 | `mssql_blitz_findings` | Advanced Diagnostics | Table | ✅ Existing |
| 14 | `mssql_blitz_cache_cpu_top10` | Advanced Diagnostics | Table | ✅ NEW |
| 15 | `mssql_blitz_snapshot_age_hours` | Advanced Diagnostics | Stat | ✅ NEW |
| 16 | `mssql_agent_status` | Critical Alerts | Stat | ✅ Existing |
| 17 | `mssql_blocking_session_count` | Locks + Critical | Time Series + Stat | ✅ Existing |
| 18 | `mssql_long_running_queries` | Connections + Critical | Time Series + Stat | ✅ Existing |
| 19 | `mssql_buffer_cache_hit_ratio` | Memory | Gauge | ✅ Existing |
| 20 | `mssql_lock_waits_total` | Locks | Time Series | ✅ Existing |
| 21 | `mssql_lock_timeouts_total` | Locks | Time Series | ✅ Existing |
| 22 | `mssql_database_state` | Database Health | Table | ✅ Existing |
| 23 | `mssql_backup_status` | Database Health | Table | ✅ Existing |
| 24 | `mssql_database_size_gb` | Database Health | Bar Chart | ✅ Existing |
| 25 | `mssql_os_memory_total_gb` | OS Memory | Stat | ✅ Existing |
| 26 | `mssql_os_memory` | OS Memory | Pie Chart + Gauge | ✅ Existing |

**Total: 26/26 metrics covered ✅**

---

## Implementation Notes

### Critical Thresholds (for DBA alerts)
```yaml
mssql_agent_status: == 0 (Critical)
mssql_deadlocks_total: rate > 0.1/s (Critical)
mssql_blocking_session_count: > 10 (Critical), > 5 (Warning)
mssql_long_running_queries: > 5 (Warning)
mssql_user_errors_total: rate > 10/s (Warning)
mssql_log_space_used_percent: > 85% (Critical), > 70% (Warning)
mssql_page_life_expectancy_seconds: < 300s (Critical), < 600s (Warning)
mssql_buffer_cache_hit_ratio: < 90% (Warning), < 80% (Critical)
mssql_io_read_latency: > 20ms (Warning), > 50ms (Critical)
mssql_io_write_latency: > 5ms (Warning - Log), > 10ms (Critical - Log)
```

### Visualization Best Practices
1. **Use Stat panels** for instant values (Agent status, Uptime, Total connections)
2. **Use Gauge** for percentage/ratio metrics (Buffer hit ratio, Memory %, Log space %)
3. **Use Time Series** for trends (Batch requests, Deadlocks, PLE, Latency)
4. **Use Table** for multi-dimensional data (Database state, Backup status, Blitz findings)
5. **Use Bar Chart** for comparisons (Database sizes)
6. **Use Pie Chart** for breakdowns (OS Memory used/available)

### Color Palette
- Health Score: Green (0-2), Yellow (3-6), Red (7+)
- Deadlocks: Green (0), Yellow (0.01-0.1), Red (>0.1)
- PLE: Red (<300), Yellow (300-600), Green (>600)
- Log Space: Green (<70%), Yellow (70-85%), Red (>85%)

---

## Next Steps
1. Review and approve this plan
2. Implement the new dashboard JSON structure
3. Test with real data
4. Create alert rules in Grafana/Prometheus based on thresholds
