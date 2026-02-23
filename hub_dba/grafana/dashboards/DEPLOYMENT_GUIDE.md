# DASHBOARD DEPLOYMENT GUIDE

Đã tạo 2 dashboards production-ready theo layout chuẩn DBA.

---

## FILES CREATED

### 1. **SQL_Server_Overview_Production.json**
Dashboard tổng quan - entry point cho tất cả instances.

**Panels:**
- **Health Score Table**: Hiển thị tất cả instances với score được tính theo weighted formula (đã FIX)
  - Clickable instance → drilldown vào Instance Detail
  - Sort by score DESC (worst first)
  - Color coding: green (0-2), yellow (3-6), red (7+)
  
- **Active Alerts**: Danh sách alerts đang firing từ Prometheus
  - Auto-refresh
  - Severity color coding
  
- **Capacity Forecast**: Dự báo database growth 30 ngày
  - Predict when disk full
  - Growth rate GB/day
  - Warning threshold

**Variables:**
- `$datasource`: Prometheus datasource selector
- `$environment`: Filter by environment (All/dev/staging/prod)

**Refresh:** 30s auto-refresh

---

### 2. **SQL_Server_Instance_Detail_Production.json**
Dashboard chi tiết cho 1 instance cụ thể.

**Panels:**

#### Row 1: Health Score
- Health score breakdown cho instance này

#### Row 2: Performance Metrics
- **Batch Requests/sec**: ✅ FIXED - dùng `rate()` cho cumulative counter
- **Deadlocks/sec**: ✅ FIXED - dùng `rate()` thay vì `increase()`
- **Page Life Expectancy**: ✅ FIXED - MIN across NUMA nodes
- **Buffer Cache Hit Ratio**: Gauge với threshold <90% = warning
- **Connections by Database**: Stacked area chart
- **SQL Agent Status**: Stat panel với color mapping
- **Long Running Queries**: Số queries >30s

#### Row 3: Memory
- **SQL Server Memory (GB)**: Resident vs Virtual
- **OS Memory Usage %**: Gauge với threshold
- **OS Memory Breakdown**: Pie chart (used/available)

#### Row 4: Locks & Blocking
- **Blocking Sessions**: Timeseries với threshold
- **Lock Waits/sec**: ✅ FIXED - dùng `rate()`
- **Lock Timeouts/sec**: ✅ FIXED - dùng `rate()`

#### Row 5: Databases
- **Database State**: Table với color mapping (Online=green, Offline=red, etc.)
  - Drilldown link vào Database Detail (future)
- **Backup Status**: Table với mapping (1=Healthy, 0=Warning, -1=Critical)
- **Database Size (GB)**: Bar chart stacked (data/log/total)

**Variables:**
- `$datasource`: Prometheus
- `$instance`: Instance selector (dynamic from Prometheus)
- `$environment`: Environment selector (dynamic based on instance)

**Refresh:** 30s auto-refresh

**Back link:** Link về Overview dashboard

---

## KEY FIXES APPLIED

### ✅ Counter Semantics
**OLD (SAI):**
```promql
increase(mssql_deadlocks[5m])  # SAI - cumulative counter không dùng increase()
```

**NEW (ĐÚNG):**
```promql
rate(mssql_deadlocks_total[5m])  # rate() cho cumulative counter
```

Áp dụng cho:
- `mssql_deadlocks_total`
- `mssql_batch_requests_total`
- `mssql_lock_waits_total`
- `mssql_lock_timeouts_total`
- `mssql_user_errors_total`
- `mssql_full_scans_total`

---

### ✅ Health Score Logic
**OLD (SAI):**
```promql
(sum by(instance) (mssql_connections) >= bool 100) * 1  # threshold arbitrary
+ (increase(mssql_deadlocks[5m]) > bool 0) * 1          # counter semantics sai
+ (mssql_blocking_session_count > bool 0) * 1          # too sensitive
+ (sum by(instance)(mssql_database_state) > bool 0) * 1 # sum enum vô nghĩa
```

**NEW (ĐÚNG):**
```promql
(sum by(instance) (mssql_connections) > bool 500) * 2     # realistic threshold + weight
+ (rate(mssql_deadlocks_total[5m]) > bool 0.1) * 3       # rate() + critical weight
+ (mssql_blocking_session_count > bool 10) * 2           # reasonable threshold
+ (count by(instance) (mssql_database_state != 0) > bool 0) * 3  # count not sum
+ (mssql_agent_status == bool 0) * 5                     # CRITICAL weight
+ (mssql_long_running_queries > bool 5) * 2
+ (mssql_page_life_expectancy_seconds < bool 300) * 2
+ (count by(instance) (mssql_backup_status{backup_type="Full"} != 1) > bool 0) * 1
```

**Changes:**
- Weighted scoring (CRITICAL issues = higher weight)
- Realistic thresholds based on production
- `count()` thay vì `sum()` cho enum metrics
- `rate()` cho cumulative counters

---

### ✅ Aggregation Scope
**OLD (SAI):**
```promql
sum(mssql_database_state)  # sum enum state vô nghĩa
```

**NEW (ĐÚNG):**
```promql
count(mssql_database_state != 0)  # đếm số DB không online
```

---

### ✅ Thresholds
Thay đổi từ arbitrary sang production-realistic:

| Metric | OLD | NEW | Reasoning |
|--------|-----|-----|-----------|
| Connections | >100 | >500 | 100 conn bình thường cho production |
| Deadlocks | >0 | >0.1/s | Deadlock 1 lần/ngày không phải critical |
| Blocking | >0 | >10 sessions | Blocking ngắn hạn bình thường |
| PLE | <300s | <300s (kept) | Rule of thumb for <16GB RAM |
| OS Memory | N/A | >90% | Standard threshold |

---

## DEPLOYMENT STEPS

### Step 1: Import Dashboards vào Grafana

```bash
# Option 1: Via Grafana UI
# 1. Login to Grafana
# 2. Dashboards → Import
# 3. Upload JSON file hoặc paste JSON content
# 4. Select Prometheus datasource
# 5. Import

# Option 2: Via API
GRAFANA_URL="http://grafana:3000"
GRAFANA_API_KEY="your-api-key"

curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @SQL_Server_Overview_Production.json

curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @SQL_Server_Instance_Detail_Production.json
```

---

### Step 2: Deploy Fixed Collectors

**QUAN TRỌNG:** Dashboard mới yêu cầu metrics từ `mssql_standard_fixed.collector.yml`.

```yaml
# prometheus.yml - update job config
scrape_configs:
  - job_name: 'sql-exporter-prod'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets:
          - '192.168.1.10:9399'  # SQL Server 1
          - '192.168.1.11:9399'  # SQL Server 2
        labels:
          environment: 'production'
          role: 'primary'
    
  - job_name: 'sql-exporter-dev'
    scrape_interval: 15s
    static_configs:
      - targets:
          - '192.168.1.27:9399'
        labels:
          environment: 'development'
          role: 'dev'
```

**sql_exporter target config:**
```yaml
# /etc/sql_exporter/targets.yml
jobs:
  - job_name: sql-server-prod-1
    collectors:
      - mssql_standard_fixed   # ← QUAN TRỌNG: dùng collector đã fix
    static_configs:
      - targets:
          server01: 'sqlserver://user:pass@192.168.1.10:1433'
        labels:
          hostname: 'SQL-PROD-01'
          role: 'primary'
          environment: 'production'
```

**Restart sql_exporter:**
```bash
systemctl restart sql_exporter
```

---

### Step 3: Verify Metrics

```bash
# Check exporter endpoint
curl http://192.168.1.10:9399/metrics | grep mssql_uptime_seconds

# Expected output:
# mssql_uptime_seconds{...} 123456

# Check Prometheus
curl http://prometheus:9090/api/v1/query?query=mssql_uptime_seconds

# Check metrics đã đổi tên (old → new):
# OLD: mssql_deadlocks (type=counter) → NEW: mssql_deadlocks_total (type=gauge)
# OLD: mssql_lock_waits (type=counter) → NEW: mssql_lock_waits_total (type=gauge)
```

**CHÚ Ý:** Nếu đang dùng collector cũ, metrics sẽ có tên `mssql_deadlocks` thay vì `mssql_deadlocks_total`.

**Giải pháp tạm:**
- Option 1: Deploy collector mới, chấp nhận data discontinuity (recommended)
- Option 2: Sửa dashboard queries thay `_total` → `` (old metrics)

---

### Step 4: Configure Alerts (Optional)

Dashboard đã có query cho Firing Alerts panel. Để alerts hoạt động, cần deploy Prometheus alert rules:

```yaml
# /etc/prometheus/rules/sql_server_alerts.yml
groups:
  - name: sql_server_critical
    interval: 30s
    rules:
      - alert: SQLAgentDown
        expr: mssql_agent_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "SQL Server Agent down on {{ $labels.instance }}"
          
      - alert: DeadlockStorm
        expr: rate(mssql_deadlocks_total[5m]) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Deadlock storm on {{ $labels.instance }}"
          
      - alert: DatabaseOffline
        expr: mssql_database_state == 6
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database {{ $labels.db }} offline"
```

Reload Prometheus:
```bash
curl -X POST http://prometheus:9090/-/reload
```

---

### Step 5: Test Drilldown Links

1. Open **SQL Server - Overview (Production)**
2. Click vào instance trong Health Score table
3. Verify drilldown vào **SQL Server - Instance Detail (Production)**
4. Verify variables `$instance` và `$environment` được truyền đúng

Nếu drilldown không hoạt động:
- Check dashboard UIDs match:
  - Overview: `sql-server-overview-prod`
  - Instance Detail: `sql-server-instance-detail`
- Check Grafana version >= 9.0 (data links feature)

---

## DASHBOARD COMPARISON

| Feature | OLD Dashboard | NEW Dashboard | Change |
|---------|---------------|---------------|--------|
| Health score formula | Simple sum, arbitrary thresholds | Weighted scoring, realistic thresholds | ✅ FIXED |
| Counter queries | `increase()` on cumulative | `rate()` on cumulative | ✅ FIXED |
| Aggregation | `sum(enum)` | `count(enum != 0)` | ✅ FIXED |
| PLE | `top(1)` - single node | `MIN()` across nodes | ✅ FIXED |
| Drilldown | Static links | Dynamic data links | ✅ IMPROVED |
| Auto-refresh | Manual | 30s auto | ✅ IMPROVED |
| Alert integration | None | Active alerts panel | ✅ NEW |
| Capacity forecast | None | 30-day prediction | ✅ NEW |

---

## KNOWN LIMITATIONS

1. **Database Detail Dashboard**: Chưa tạo (future work)
   - Drilldown link từ Database State panel sẽ 404
   - Cần tạo dashboard với Top Queries, Index Fragmentation, File IO

2. **Blocking Detail**: Chưa có trong Instance Detail
   - Cần deploy `mssql_advanced.collector.yml` để có `mssql_blocking_detail_wait_ms`
   - High cardinality → cân nhắc scrape interval dài (60s)

3. **Wait Stats**: Chưa có
   - Cần deploy `mssql_advanced.collector.yml`

4. **Metric Naming**: Dashboard giả định metrics có suffix `_total`
   - Nếu dùng collector cũ, cần sửa queries (xem Step 3)

---

## TROUBLESHOOTING

### Dashboard không hiển thị data

**Check:**
```promql
# Prometheus query explorer
mssql_uptime_seconds
```

**Nếu empty:**
- Check sql_exporter target config
- Check exporter logs: `journalctl -u sql_exporter -f`
- Check SQL Server permissions (VIEW SERVER STATE, VIEW ANY DEFINITION)

---

### Health score = 0 cho tất cả instances (false)

**Nguyên nhân:** Prometheus chưa có đủ data (mới start lại).

**Giải pháp:** Đợi 2-3 scrape intervals (30-45s).

**Verify:**
```promql
rate(mssql_deadlocks_total[5m])
# Nếu no data → metric mới, chưa có 5m history
```

---

### Drilldown link 404

**Check:**
1. Dashboard UID đúng không?
   - Overview dashboard link: `/d/sql-server-instance-detail/...`
   - Instance Detail dashboard UID: `sql-server-instance-detail`
   
2. Variables được truyền không?
   - Check URL: `?var-instance=...&var-environment=...`

---

### Panel "No data"

**Possible causes:**
1. Metric name mismatch (old `mssql_deadlocks` vs new `mssql_deadlocks_total`)
2. Label filter sai (`$instance` variable empty)
3. Collector chưa deploy

**Debug:**
- Remove filters, query raw metric: `mssql_deadlocks_total`
- Check available labels: `label_values(mssql_uptime_seconds, instance)`

---

## NEXT STEPS

1. **Week 1**: Deploy Overview + Instance Detail dashboards
2. **Week 2**: Deploy `mssql_advanced.collector.yml`, add Wait Stats panel
3. **Week 3**: Create Database Detail dashboard
4. **Week 4**: Setup Prometheus recording rules (pre-compute health score)
5. **Month 2**: Setup alerting (Alertmanager integration)

---

## FEEDBACK & ITERATION

Dashboard này là v1.0 dựa trên audit findings. Cần thu thập feedback từ DBA team:

- Threshold có hợp lý với production workload không?
- Thiếu metric nào quan trọng?
- Panel nào dư thừa?
- Cần thêm aggregation nào?

Iterate based on real-world usage.
