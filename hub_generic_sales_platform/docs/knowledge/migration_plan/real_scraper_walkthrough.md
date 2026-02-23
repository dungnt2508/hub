# Walkthrough - Real AI Web Scraper (Live Implementation)

Tôi đã chính thức loại bỏ Mock data và triển khai bộ máy **AI Scraper chạy thật** cho hệ thống của bạn.

## Các thành phần đã triển khai

### 1. Scraping Engine (Playwright)
- Sử dụng **Playwright** để giả lập trình duyệt, cho phép đọc nội dung từ bất kỳ website nào, kể cả các trang web sử dụng React/Next.js hoặc có cơ chế bảo vệ cơ bản.
- Tự động trích xuất nội dung văn bản (InnerText) để tối ưu hóa lượng Token gửi cho AI.

### 2. AI Brain (LLM Parser)
- Kết nối trực tiếp với **LLMService** (OpenAI/LiteLLM).
- Sử dụng hệ thống Prompt thông minh để bóc tách dữ liệu thô thành cấu trúc chuẩn:
    - `name`, `description`, `code`.
    - `variants` (Màu sắc, kích cỡ, giá tiền).
    - Toàn bộ được định dạng JSON chuẩn để import vào Catalog.

### 3. Quy trình vận hành Real-time
- **Back-end**: Thay thế `MockWebScraperProvider` bằng `RealWebScraperProvider`.
- **API**: Tích hợp luồng chạy ngầm (Background Tasks) để người dùng không phải chờ đợi lâu trên giao diện.

## Cách sử dụng thực tế
1. **Cài đặt môi trường**: Chạy lệnh `pip install -r requirements.txt` và `playwright install chromium`.
2. **Khởi chạy**:
    - Vào trang `/migration`.
    - Nhập đường dẫn sản phẩm thật (ví dụ: một trang từ Tiki, Shopee hoặc website bất kỳ).
    - Nhấn **Start Scraping**.
3. **Kết quả**: Hệ thống sẽ cào web -> AI bóc tách -> Chuyển sang `staged`. Bạn có thể nhấn **Preview** để thấy dữ liệu thật từ website đó!

## Lưu ý kỹ thuật
- Để đạt hiệu quả cao nhất, hãy đảm bảo `OPENAI_API_KEY` trong file `.env` của bạn đang hoạt động và có đủ hạn mức.
- Dung lượng text gửi cho AI hiện được giới hạn ở 15,000 ký tự đầu tiên để tránh lỗi tràn Token nhưng vẫn đảm bảo lấy đủ thông tin chính.

---
**Hệ thống Migration Hub của bạn giờ đây đã thực sự "thông minh" và có thể tự động hóa việc nhập liệu từ thế giới bên ngoài!**
