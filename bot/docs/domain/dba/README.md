DBA DOMAIN
==========

Domain phân tích hiệu năng, tối ưu, giám sát cơ sở dữ liệu.

DOMAIN PURPOSE
--------------

Xử lý các tác vụ quản trị cơ sở dữ liệu:
- Phân tích slow query
- Kiểm tra index health
- Phát hiện blocking
- Phân tích wait stats
- Phân tích query regression
- Phát hiện deadlock pattern
- Phân tích I/O pressure
- Dự báo dung lượng
- Validate custom SQL
- So sánh sp_Blitz vs custom
- Phân loại incidents

DOMAIN TYPE
-----------

BUSINESS

OPERATION domain với discrete intents.

INTERACTION MODE
----------------

COMMAND

Nhận input → thực thi → trả kết quả.

Không giữ state dài.

Mỗi request độc lập.

ENTRY POINT
-----------

DBAEntryHandler.handle()

Router gửi DomainRequest với:
- intent: tên intent (ví dụ: "analyze_slow_query")
- slots: dữ liệu cần thiết (ví dụ: query_id, database_name)

EntryHandler map intent → use case → execute.

ALLOWED RESPONSIBILITIES
------------------------

- Xử lý intent từ router.
- Map intent → use case.
- Thực thi use case.
- Trả DomainResponse với result.
- Validate slots.
- Kết nối database qua MCP client.
- Phân tích, tối ưu, giám sát database.

FORBIDDEN RESPONSIBILITIES
--------------------------

- Gọi trực tiếp domain khác.
- Quyết định routing domain.
- Giữ state hội thoại dài.
- Phụ thuộc vào frontend.
- Xử lý logic nghiệp vụ ngoài DBA.

EXIT CONDITIONS
---------------

Domain trả response khi:
- Use case thực thi xong (SUCCESS).
- Use case lỗi (ERROR).
- Thiếu slots (NEED_MORE_INFO).

Domain không tự chuyển domain.

User muốn chuyển domain → gửi message mới → Router xử lý.

INTENTS
-------

analyze_slow_query
- Phân tích các query chạy chậm.
- Required slots: query_id, database_name.

check_index_health
- Kiểm tra sức khỏe index.
- Required slots: database_name, table_name.

detect_blocking
- Phát hiện blocking queries.
- Không cần slots.

analyze_wait_stats
- Phân tích wait statistics.
- Required slots: database_name.

analyze_query_regression
- Phân tích query regression.
- Required slots: query_id, time_range.

detect_deadlock_pattern
- Phát hiện deadlock pattern.
- Không cần slots.

analyze_io_pressure
- Phân tích I/O pressure.
- Required slots: database_name.

capacity_forecast
- Dự báo dung lượng.
- Required slots: database_name, forecast_period.

validate_custom_sql
- Kiểm tra SQL queries tùy chỉnh.
- Required slots: sql_query, database_name.

compare_sp_blitz_vs_custom
- So sánh sp_Blitz vs custom queries.
- Required slots: query_type, database_name.

incident_triage
- Phân loại và phân tích incidents.
- Required slots: incident_id, severity.

get_active_alerts
- Lấy danh sách alerts đang hoạt động.
- Không cần slots.

store_query_metrics
- Lưu trữ metrics query.
- Required slots: query_id, metrics.
