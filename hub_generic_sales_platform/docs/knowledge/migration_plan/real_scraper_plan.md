# Implementation Plan - Real AI Web Scraper

Replace the mock scraper with a fully functional implementation using Playwright for web fetching and LLMs for structured data tructuring.

## User Review Required

> [!IMPORTANT]
> - Hệ thống sẽ cài đặt thêm thư viện `playwright` (~200MB cho browser engine).
> - Quá trình cào web phụ thuộc vào độ phức tạp của trang web và hạn mức API LLM (OpenAI) của bạn.
> - Chi phí token có thể phát sinh tùy thuộc vào lượng nội dung AI cần phân tích.

## Proposed Changes

### Environment Setup
- Cài đặt `playwright`.
- Run `playwright install chromium` (headless mode).

### [NEW] Scraping Service
#### [scraping_service.py](file:///d:/project%20python/hub/bot_v4/app/core/services/scraping_service.py)
- Sử dụng Playwright để lấy nội dung HTML của URL.
- Trích xuất Text content hoặc HTML thô một cách thông minh (giới hạn token).

### [NEW] AI Parser Service
#### [ai_parser_service.py](file:///d:/project%20python/hub/bot_v4/app/core/services/ai_parser_service.py)
- Kết nối với `LLMService`.
- Sử dụng System Prompt chuyên dụng để bóc tách:
    - `name`, `description`, `code`.
    - `variants` (SKU, Name, Price).
    - `attributes`.

### [MODIFY] Migration Providers
#### [migration_providers.py](file:///d:/project%20python/hub/bot_v4/app/core/services/migration_providers.py)
- Thay thế `MockWebScraperProvider` bằng logic thực tế gọi qua `ScrapingService` và `AIParserService`.

## Verification Plan

### Automated Tests
- Chạy cào thử một URL sản phẩm thực tế (ví dụ: một trang máy tính hoặc thời trang).
- Kiểm tra dữ liệu trả về có đúng định dạng JSON Staged không.

### Manual Verification
- Sử dụng giao diện Migration Hub để nhập URL thật.
- Kiểm tra quá trình "Processing" ngầm và xem kết quả trong bảng Migration History.
