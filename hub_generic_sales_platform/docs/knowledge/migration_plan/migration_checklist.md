# Checklist Triển khai: Web Scraper Migration Option

Bản checklist này giúp bạn bám sát lộ trình xây dựng tính năng Migrate từ Web bằng AI, đảm bảo dữ liệu ổn định từ lúc cào đến lúc vào DB chính thức.

---

## 1. Tầng Schema (Database)
Cần quản lý trạng thái của các đợt migrate vì việc cào web tốn thời gian (async).

- [ ] **Table `migration_job`**: Lưu thông tin phiên migrate.
    - `id`, `tenant_id`, `bot_id`, `domain_id`.
    - `source_url`: Link nguồn.
    - `type`: "web_scraper" (để mở rộng Excel sau này).
    - `status`: [PENDING, CRAWLING, PARSING, COMPLETED, FAILED].
    - `raw_data`: (JSON) Chứa HTML hoặc Text thô sau khi cào (để debug).
    - `staged_data`: (JSON) Chứa kết quả JSON sau khi AI bóc tách (để Preview).
    - `error_log`: Lưu lỗi nếu cào/AI thất bại.
- [ ] **Khả năng quan hệ**: Đảm bảo schema hỗ trợ link từ `staged_data` về các `AttributeDefinition` hiện có.

---

## 2. Tầng Backend (API & Logic)

- [ ] **Scraping Engine (Tầng Fetching)**:
    - [ ] Tích hợp `Playwright` hoặc `Firecrawl` để lấy nội dung Web.
    - [ ] Cơ chế xử lý Timeout (nếu Web khách quá chậm).
    - [ ] Hỗ trợ lấy danh sách ảnh sản phẩm (Media).
- [ ] **AI Parser (Tầng Bóc tách)**:
    - [ ] Xây dựng Prompt "Product Extraction": Hướng dẫn LLM chuyển Markdown/Text thành JSON Schema của Hub.
    - [ ] Logic lấy giá: Tự động xóa ký tự đợn vị, đổi thành số (`"2.500.000đ"` -> `2500000`).
    - [ ] Logic SKU: Gợi ý SKU dựa trên tên sản phẩm nếu Web không có SKU rõ ràng.
- [ ] **API Endpoints**:
    - [ ] `POST /catalog/migrate/scrape`: Nhận URL, tạo Job và bắt đầu cào (trả về `job_id`).
    - [ ] `GET /catalog/migrate/jobs/{id}`: Kiểm tra trạng thái và lấy dữ liệu nháp (`staged_data`).
    - [ ] `POST /catalog/migrate/confirm/{id}`: API quan trọng nhất - Đưa dữ liệu từ nháp vào bảng `Product`, `Version`, `Variant` chính thức.
- [ ] **Background Tasks**:
    - [ ] Dùng `BackgroundTasks` của FastAPI (hoặc Celery nếu làm lớn) để việc cào web không làm treo UI của khách.

---

## 3. Tầng Frontend (UI/UX)

- [ ] **Giao diện nhập liệu (Input)**:
    - [ ] Nút "Import from Website" trong trang Catalog.
    - [ ] Modal nhập URL + Chọn Bot/Domain mục tiêu.
- [ ] **Màn hình Preview (Xác nhận dữ liệu)**:
    - [ ] Hiển thị danh sách sản phẩm AI đã "đọc" được.
    - [ ] Cho phép chỉnh sửa trực tiếp (Inline Edit) nếu AI bóc tách sai Tên hoặc Giá.
    - [ ] **Mapping Attributes**: UI cho phép chọn: "Thông số 'Vật liệu' này sẽ map vào Attribute 'Material' của tôi".
- [ ] **Tiến trình (Progress Indicators Management)**:
    - [ ] Hiển thị Spinner hoặc Progress Bar: "Đang cào dữ liệu..." -> "Đang dùng AI phân tích..."
- [ ] **Xử lý lỗi**: Hiển thị thông báo nếu Web bị chặn (Bot detection) hoặc AI không tìm thấy sản phẩm.

---

## 4. Quản lý rủi ro (Advanced)

- [ ] **User-Agent Rotation**: Tránh bị Website khách hàng chặn (Proxy/User-Agent).
- [ ] **Cost Control**: Giới hạn số lượng URL khách được cào mỗi lần để tránh tốn phí API LLM (Token count).
- [ ] **Image Proxy**: Download ảnh về server của mình (S3/Cloudinary) thay vì chỉ lưu Link Web khách (vì link web khách có thể die sau này).

---

**Lưu ý**: Bạn nên bắt đầu với **Giai đoạn 1: Chỉ cào 1 trang sản phẩm lẻ** trước khi làm cào toàn bộ Website (Sitemap). Điều này giúp bạn kiểm soát chất lượng AI Parser tốt hơn.
