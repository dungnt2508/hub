# Báo cáo Audit Tổng hợp: Runtime & Logic Intelligence

**Trạng thái**: 🔴 CẦN KHẮC PHỤC NGAY LẬP TỨC
**Vấn đề cốt lõi**: Bot có "dữ liệu" (History, Slots) nhưng "bộ não" (LLM) không được phép truy cập.

## 1. Các Lỗ hổng Trí tuệ (Intelligence Gaps)

### A. Lỗ hổng Mất trí nhớ (Amnesia Bug) - 🔴 Critical
*   **Mô tả**: Bot không nhớ những gì vừa nói ở câu trước.
*   **Nguyên nhân kỹ thuật**:
    *   File `OpenAIProvider.py`: Hàm `generate_response` hardcode danh sách tin nhắn chỉ gồm `[System, User]`.
    *   `AgentOrchestrator.py`: Có lấy history từ DB nhưng không có cách nào truyền vào `OpenAIProvider`.
*   **Hậu quả**: Không thể thực hiện hội thoại đa vòng (multi-turn conversation).

### B. Lỗ hổng Mù Context (Context Blindness) - 🔴 Critical
*   **Mô tả**: Bot không biết khách hàng đang chọn sản phẩm nào (Slot).
*   **Nguyên nhân kỹ thuật**:
    *   `AgentOrchestrator.py`: Context Slots (VD: `product=Mazda`) được lấy lên nhưng **không được inject vào System Prompt**.
    *   Các Tool (`search`, `details`) chỉ nhận tham số text thô, không tự động fallback vào Slot.
*   **Hậu quả**: Khách phải lặp lại tên sản phẩm trong mỗi câu hỏi.

### C. Máy Trạng thái "Nhà Tù" (Rigid State Machine) - 🟠 Major
*   **Mô tả**: Bot từ chối thực hiện tác vụ đơn giản vì đang ở trạng thái khác.
*   **Nguyên nhân kỹ thuật**:
    *   `state_machine.py`: Quy định tool theo whitelist quá chặt. Ví dụ: `PURCHASING` không được dùng `search_offerings`.
*   **Hậu quả**: Trải nghiệm người dùng bị đứt gãy, cảm giác máy móc.

### D. Thiếu cơ chế phục hồi (No Error Recovery) - 🟡 Minor
*   **Mô tả**: Nếu LLM lỗi (timeout/overload), bot trả về thông báo lỗi kỹ thuật thô (`Error: ...`) thay vì câu xin lỗi khéo léo.
*   **Nguyên nhân**: `OpenAIProvider` catch exception nhưng trả về raw string.

## 2. Checklist Triển khai Sửa lỗi (Implementation Plan)

### Bước 1: Fix Core LLM Provider (Nền móng)
- [ ] **Sửa `OpenAIProvider.generate_response`**:
    - [ ] Thêm tham số `messages_history: List[Dict]`.
    - [ ] Chèn history vào giữa System Prompt và User Message.

### Bước 2: Fix "Bộ não" Orchestrator
- [ ] **Sửa `AgentOrchestrator.run`**:
    - [ ] Inject `Context Slots` vào `System Prompt` (Format: `CONTEXT: {key: value}`).
    - [ ] Truyền `conversation_history` vào hàm `generate_response` mới.
    - [ ] Cập nhật System Prompt để hướng dẫn bot ưu tiên dùng Slot khi user không nói rõ đối tượng.

### Bước 3: Nới lỏng State Machine
- [ ] **Sửa `state_machine.py`**:
    - [ ] Cho phép `search_offerings` và `get_offering_details` hoạt động ở **TẤT CẢ** các trạng thái (Global Tools).

### Bước 4: Nâng cấp Tool (Thông minh hơn)
- [ ] **Sửa `CatalogStateHandler`**:
    - [ ] Tool `handle_get_offering_details`: Nếu thiếu `offering_code`, tự động lấy từ Slot `offering_id` hoặc `product_id`.

## 3. Đánh giá sau sửa lỗi
Sau khi thực hiện 4 bước trên, bot sẽ:
1.  Nhớ được hội thoại cũ.
2.  Hiểu context ngầm (Vd: "Giá bao nhiêu?" -> Hiểu là giá của xe vừa chọn).
3.  Linh hoạt xử lý tình huống bất ngờ.
