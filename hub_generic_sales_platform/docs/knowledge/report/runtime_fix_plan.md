# Kế hoạch Triển khai Sửa lỗi Runtime (Intelligence Fix)

Mục tiêu: "Chữa bệnh" Mất trí nhớ và Mù Context cho Bot.

## Bước 1: Fix Core LLM Provider (Nền móng) ✅
- [x] **Sửa `OpenAIProvider.generate_response`**:
    - [ ] Thêm tham số `messages_history: List[Dict]`.
    - [ ] Chèn history vào giữa System Prompt và User Message.

## Bước 2: Fix "Bộ não" Orchestrator ✅
- [x] **Sửa `AgentOrchestrator.run`**:
    - [ ] Inject `Context Slots` vào `System Prompt` (Format: `CONTEXT: {key: value}`).
    - [ ] Truyền `conversation_history` vào hàm `generate_response` mới.
    - [ ] Cập nhật System Prompt để hướng dẫn bot ưu tiên dùng Slot khi user không nói rõ đối tượng.

## Bước 3: Nới lỏng State Machine ✅
- [x] **Sửa `state_machine.py`**:
    - [ ] Cho phép `search_offerings` và `get_offering_details` hoạt động ở **TẤT CẢ** các trạng thái (Global Tools).

## Bước 4: Nâng cấp Tool (Thông minh hơn) ✅
- [x] **Sửa `CatalogStateHandler`**:
    - [ ] Tool `handle_get_offering_details`: Nếu thiếu `offering_code`, tự động lấy từ Slot `offering_id` hoặc `product_id`.

## Verification Steps
1.  **Test Amnesia**:
    - User: "Tôi tìm xe Vios."
    - Bot: "Vios có giá..."
    - User: "Nó có màu đỏ không?" -> Bot phải hiểu "Nó" là Vios.
2.  **Test Context Blindness**:
    - User: "Tôi chọn cái xe màu đỏ." (Slot: Red)
    - User: "Giá bao nhiêu?" -> Bot phải trả lời giá của xe Red.
3.  **Test Rigidity**:
    - Vào flow Chốt đơn.
    - User hỏi lại thông số kỹ thuật -> Bot phải trả lời được (không báo lỗi).
