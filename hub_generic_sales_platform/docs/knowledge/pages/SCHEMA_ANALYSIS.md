# ĐÁNH GIÁ MỨC ĐỘ "DATA-DRIVEN" CỦA SCHEMA (SCHEMA ANALYSIS)

Dựa trên file `alembic/versions/001_initial_schema.py`, dưới đây là phân tích về khả năng **Data-Driven** của kiến trúc hiện tại.

## 1. KẾT LUẬN CHUNG: ĐẠT 90% (XUẤT SẮC)
Schema này **hoàn toàn đáp ứng đủ** cho một nền tảng "Generic Sales Platform" hiện đại. Nó được thiết kế để "cấu hình hóa" thay vì "cứng hóa" (Hard-coding), cho phép hệ thống mở rộng sang nhiều ngành hàng (Bất động sản, Bán lẻ, Dịch vụ) mà không cần sửa code database.

---

## 2. CÁC ĐIỂM SÁNG ("DATA-DRIVEN" HIGHLIGHTS)

### ✅ 1. Tính Động của Dữ liệu (Dynamic Ontology)
*Thay vì tạo bảng `RealEstate`, `Fashion`, `Loan`, bạn dùng mô hình EAV (Entity-Attribute-Value) cải tiến.*
*   **Bằng chứng:** `domain_attribute_definition`, `tenant_attribute_config`, `tenant_offering_attribute_value`.
*   **Ý nghĩa:** Hôm nay bán áo thun (Size, Màu), ngày mai bán đất (Hướng, Diện tích), ngày kia bán gói vay (Lãi suất) -> **Chỉ cần thêm dòng vào Database, không cần sửa Code.**

### ✅ 2. AI-Native & Vector Ready
*Schema được thiết kế sẵn cho RAG và Semantic Search.*
*   **Bằng chứng:** Column `embedding vector(1536)` xuất hiện ở khắp nơi:
    *   `tenant_offering_version`: Để tìm kiếm sản phẩm bằng ngôn ngữ tự nhiên.
    *   `tenant_semantic_cache`: Để cache câu trả lời Bot, tiết kiệm tiền OpenAI.
    *   `bot_faq`: Để tìm câu hỏi tương đồng.

### ✅ 3. Observability cực sâu (Deep Traceability)
*Mọi quyết định của Bot đều được ghi lại để phân tích.*
*   **Bằng chứng:**
    *   `runtime_decision_event`: Ghi lại tại sao Bot chọn Tool này? Mất bao nhiêu ms? Tốn bao nhiêu Token? -> **Dùng để tối ưu chi phí.**
    *   `runtime_guardrail_check`: Ghi lại Bot có vi phạm chính sách không? -> **Dùng để Audit an toàn.**

### ✅ 4. Cấu hình nằm trong Data (Config-as-Data)
*Hành vi của Bot được quy định bởi dữ liệu JSON, không phải logic if/else trong code.*
*   **Bằng chứng:**
    *   `knowledge_domain.flow_config`: Quy định luồng đi của từng ngành hàng.
    *   `bot_version.flow_config`: Quy định kịch bản của từng phiên bản Bot.
    *   `tenant_attribute_config.ui_config`: Quy định cách hiển thị trên Frontend (Dropdown/Checkbox).

---

## 3. MỘT SỐ ĐIỂM CÓ THỂ CẢI THIỆN (MINOR GAPS - FOR V5)

Tuy đã rất tốt, nhưng nếu muốn "Perfect", có thể cân nhắc các điểm sau (nhưng **không chặn** việc phát triển hiện tại):
1. ...

2.  **User Feedback Loop (Vòng lặp phản hồi):**
    *   Hiện tại: Chưa thấy bảng lưu Like/Dislike cụ thể cho từng câu trả lời để Fine-tune model.
    *   Giải pháp tạm: Lưu vào `runtime_turn.ui_metadata`.

3.  **A/B Testing Experiment:**
    *   Hiện tại: Có `bot_version`, có thể test thủ công.
    *   Tương lai: Cần bảng `experiment` để tự động chia traffic 50/50 và đo hiệu quả.

---

## 4. LỜI KHUYÊN CHO DEV TEAM

*   **Đừng sửa Schema nữa!** Nó đã quá đủ cho giai đoạn này.
*   Hãy tập trung viết API để đổ dữ liệu vào các bảng `configuration` và `attribute` càng sớm càng tốt, vì sức mạnh của hệ thống này nằm ở dữ liệu cấu hình.
