# Kế hoạch Kiểm tra & Triển khai Hệ thống Catalog và Bot

## Tổng quan Kiến trúc
Hệ thống bao gồm hai thành phần chính:
1. **Catalog Service** (TypeScript/Node): Backend quản lý sản phẩm (quy trình - workflows, công cụ - tools, tích hợp - integrations). Sử dụng cơ sở dữ liệu PostgreSQL với logic nghiệp vụ (business logic) đang bị rò rỉ vào tầng service.
2. **Bot Service** (Python): Chatbot đa miền (multi-domain) sử dụng RAG cho các truy vấn liên quan đến danh mục sản phẩm.

Kiến trúc hiện tại đủ dùng cho các tìm kiếm cơ bản nhưng thiếu cấu trúc và trí tuệ cần thiết cho việc quản lý danh mục quy mô production và trả lời câu hỏi khách hàng với độ chính xác tuyệt đối.

## Các Vấn đề & Kết quả Kiểm tra

### [BLOCKER] Thiết kế Domain Catalog Quá Đơn giản
Domain Catalog hiện tại đang quá phẳng và thiếu sức mạnh (anemic).
- **Thiếu Category**: Hiện chỉ hỗ trợ các `tags` không có cấu trúc.
- **Không có Variant/SKU**: Không hỗ trợ các phiên bản sản phẩm (ví dụ: các gói khác nhau của một công cụ, các phiên bản khác nhau với giá khác nhau).
- **Thuộc tính Không Cấu trúc**: Metadata của sản phẩm được lưu dưới dạng `JSONB` chung chung mà không có định nghĩa schema cụ thể cho từng loại sản phẩm.

### [CRITICAL] Cơ chế Tìm kiếm (RAG) của Bot Quá Sơ sài
Bot hiện tại hoàn toàn phụ thuộc vào tìm kiếm vector (semantic search).
- **Mù tịt về Ý định (Intent Blindness)**: Bot không phân loại được khách hàng đang hỏi về một thuộc tính cụ thể (ví dụ: "Giá bao nhiêu?") hay đang tìm kiếm sản phẩm chung chung.
- **Dữ liệu Không Chính xác**: LLM có thể bị ảo giác dựa trên các kết quả vector trùng lặp nhưng không phải là sự thực (ví dụ: gán nhãn "Miễn phí" cho sản phẩm "Có phí" vì mô tả có nhắc tới "Dùng thử miễn phí").
- **Vi phạm Tính Nghiêm ngặt**: Prompt chưa ép buộc bot chỉ được trả lời dựa trên dữ liệu thực tế 100%.

### [HIGH] Rò rỉ Logic Nghiệp vụ
- `ProductService.ts` chứa hơn 500 dòng code bao gồm kiểm tra tính hợp lệ, chuyển đổi trạng thái, và phát hiện thay đổi quan trọng. Những logic này lẽ ra nên được đóng gói trong Domain Model (Rich Domain Model).

---

## Các Thay đổi Đề xuất

### 1. Chuẩn hóa Domain Catalog (DDD Thực dụng)
Chúng ta sẽ đưa vào một domain model cấu trúc hơn để đáp ứng các yêu cầu quản lý danh mục chuyên nghiệp.

#### [MODIFY] [Product Repository](file:///g:/project%20python/hub/catalog/backend/src/repositories/product.repository.ts)
- Cập nhật `findMany` để hỗ trợ các bộ lọc chi tiết hơn (khoảng giá, thuộc tính cấu trúc).

#### [NEW] [Category Migration](file:///g:/project%20python/hub/catalog/backend/migrations/016_create_categories_table.sql)
- Tạo bảng `categories` hỗ trợ phân cấp (hierarchy).
- Liên kết `products` với `categories`.

#### [NEW] [Attribute Schema](file:///g:/project%20python/hub/catalog/backend/migrations/017_create_attributes_table.sql)
- Định nghĩa `attribute_definitions` theo từng category để đảm bảo tính nhất quán của dữ liệu.

---

### 2. Nâng cấp Trí tuệ cho Bot (Intent-Aware Hybrid Search)
Chúng ta sẽ chuyển dịch bot từ hướng "RAG thuần túy" sang hướng "Logic-First" (Logic là ưu tiên).

#### [NEW] [Catalog Intent Classifier](file:///g:/project%20python/hub/bot/backend/domain/catalog/intent_classifier.py)
- Sử dụng LLM để phân loại tin nhắn người dùng thành các ý định cụ thể:
  - `PRODUCT_SEARCH`: Tìm kiếm chung.
  - `PRODUCT_SPECIFIC_INFO`: Hỏi giá, tình trạng hàng, hoặc thông số của một sản phẩm cụ thể.
  - `PRODUCT_COMPARISON`: So sánh hai hoặc nhiều sản phẩm.
  - `PRODUCT_COUNT`: Đếm số lượng sản phẩm trong một danh mục.

#### [MODIFY] [Catalog Knowledge Engine](file:///g:/project%20python/hub/bot/backend/knowledge/catalog_knowledge_engine.py)
- Triển khai **Hybrid Search**: Dựa vào ý định đã phân loại để quyết định dùng Vector Search, Truy vấn chính xác vào DB, hoặc cả hai.
- **Strict Prompting**: Cập nhật RAG prompt sử dụng hệ thống câu lệnh phòng vệ, buộc bot phải dựa hoàn toàn vào dữ liệu.

#### [MODIFY] [Catalog Entry Handler](file:///g:/project%20python/hub/bot/backend/domain/catalog/entry_handler.py)
- Tích hợp `IntentClassifier`.
- Điều phối luồng phản hồi dựa trên ý định được phát hiện.

---

## Kế hoạch Xác minh

### Kiểm thử Tự động
- Chạy `pytest bot/backend/tests` để đảm bảo không lỗi các luồng hiện tại.
- Tạo bộ kiểm thử mới `bot/backend/tests/test_catalog_bot.py` tập trung vào các tình huống:
  - Truy vấn giá (xác minh với dữ liệu giả lập DB).
  - Truy vấn ngoài danh mục (phải trả lời "Tôi không biết").
  - Truy vấn so sánh.

### Xác minh Thủ công
- Thử nghiệm qua giao diện bot với các câu hỏi lắt léo như "Những sản phẩm nào miễn phí mà có tính năng AI?" để kiểm tra khả năng lọc hybrid.
