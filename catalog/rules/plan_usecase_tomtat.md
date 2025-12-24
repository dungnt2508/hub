System: Bạn là trợ lý lập trình, nhiệm vụ là TRIỂN KHAI USECASE “TÓM TẮT ĐA NGUỒN”

Yêu cầu : 

1. Pipeline xử lý

Backend nhận input: URL / RSS / File.

Tải nội dung (crawler hoặc parser).

Làm sạch text (HTML → plain text).

Gửi vào LLM cùng persona user.

Nhận JSON gồm summary + insights + data_points.

Lưu DB.

Render UI + gửi email nếu là lịch trình.

2. Thành phần

API tóm tắt.

Module crawl URL.

Module đọc RSS.

Module parse file PDF/DOCX/TXT.

Persona engine (lấy cấu hình user).

Scheduler (cron hoặc n8n).

Email sender.

Dashboard để xem danh sách tóm tắt + chi tiết.

3. Kiến trúc

Frontend → gọi Backend → Backend xử lý → gọi AI Service → trả JSON → DB.

N8n chạy xử lý định kỳ: fetch RSS, tóm tắt, gửi mail.

Storage lưu file upload.

DB lưu metadata + summary + bảng số liệu.


4. DB SCHEMA (TÓM TẮT)

User
- id
- email
- password_hash
- persona_json
- created_at

Article
- id
- user_id
- source_type   (url | rss | file)
- source_value  (URL/RSS link/file path)
- title
- raw_text
- metadata_json
- created_at

Summary
- id
- article_id
- summary_text
- insights_json
- data_points_json
- created_at

Schedule
- id
- user_id
- source_type
- source_value
- frequency (hourly|daily|weekly)
- active

5. MỨC ĐỘ TRIỂN KHAI

Backend có thể chạy tóm tắt đồng bộ nếu bài ngắn, async nếu bài lớn.

Không cần microservice; AI gọi API ngoài.

Khi traffic tăng mới tách ML/AI Service riêng.