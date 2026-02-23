# Application Services (Modular Tools & Handlers)

Thư mục này chứa các dịch vụ xử lý nghiệp vụ được thiết kế theo hướng module hóa, phục vụ cho kiến trúc **Hybrid Orchestration (Sprint 2)**.

## 📌 Tổng quan


## 📂 Danh sách các dịch vụ

### 1. Quản lý Agent & Tools
*   **`agent_tool_registry.py`**: Registry trung tâm để đăng ký các hàm Python thành công cụ (tool) mà LLM có thể nhận diện và gọi.
*   **`catalog_state_handler.py`**: Xử lý logic nghiệp vụ Catalog. Cung cấp các công cụ:
    *   `search_products`: Liệt kê sản phẩm.
    *   `get_product_details`: Xem chi tiết giá/thông số.
    *   `compare_products`: So sánh sản phẩm.
*   **`integration_handler.py`**: Xử lý tích hợp với hệ thống bên ngoài. Cung cấp:
    *   `trigger_web_hook`: Kích hoạt Webhook (n8n, Make).

### 2. Quản lý trạng thái (State & Context)
*   **`session_state.py`**: Dịch vụ hỗ trợ đọc và quản lý trạng thái phiên hội thoại (`ConversationSession`), bao gồm Metadata và Role của người dùng.
*   **`slot_extractor.py`**: Sử dụng LLM để trích xuất các thông tin có cấu trúc (Entity) từ câu nói của người dùng.
*   **`slot_normalizer.py`**: Chuẩn hóa dữ liệu slot (ví dụ: chuyển "20 triệu" thành số `20000000`).
*   **`slot_validator.py`**: Kiểm tra tính hợp lệ và đầy đủ của các thông tin đã trích xuất.

### 3. Bảo mật & Kiểm soát
*   **`guardrail_checker.py`**: Kiểm tra tính an toàn của yêu cầu trước khi xử lý sâu hơn (chống Prompt Injection, lọc từ ngữ nhạy cảm).

---

## 🛠 Cách sử dụng (Tư duy mới 2026)
Thay vì gọi tuần tự, các service này nên được tích hợp vào `AgentOrchestrator` thông qua `agent_tools`:

```python
# Ví dụ đăng ký một service làm tool
@agent_tools.register_tool(name="extract_user_info", description="...")
async def handle_extraction(...):
    # Logic từ SlotExtractor
    pass
```
## 🧰 Danh sách Tools hiện có (Agentic Path)

Dưới đây là các công cụ đã được đăng ký và sẵn sàng cho Agent sử dụng:

| Tên Tool | Mô tả | File |
| :--- | :--- | :--- |
| `search_products` | Tìm kiếm hoặc liệt kê toàn bộ sản phẩm đang hoạt động. | `catalog_state_handler.py` |
| `get_product_details` | Truy vấn giá cả, tính năng chi tiết của s.phẩm qua mã. | `catalog_state_handler.py` |
| `compare_products` | So sánh thông số giữa 2 hoặc nhiều sản phẩm. | `catalog_state_handler.py` |
| `trigger_web_hook` | Kích hoạt Webhook bên ngoài (n8n, Make) để thực hiện task. | `integration_handler.py` |
