# 🧠 CHÍNH SÁCH SỬ DỤNG INTENT (INTENT USAGE POLICY)

**Phiên bản:** 1.0 (2026)  
**Phạm vi áp dụng:** Hybrid Orchestration (LLM + Finite State Machine)

---

## 🎯 NGUYÊN TẮC CỐT LÕI (STATE-FIRST)

Trong hệ thống IRIS Hub v4, **State dictate all (Trạng thái quyết định tất cả)**. AI không tự ý nhảy luồng (Flow) mà chỉ đề xuất hành động dựa trên Input của người dùng.

1.  **AI đề xuất (Suggest):** LLM phân tích câu chat và trả về một `intent` (với confidence).
2.  **Hệ thống quyết định (Decide):** `FlowDecisionService` đối chiếu `intent` đó với `current_state`.
3.  **Hành động (Act):** Nếu transition hợp lệ, state mới được cập nhật và Tool tương ứng được thực thi.

---

## ✅ KHI NÀO NÊN DÙNG INTENT?

Intent chỉ nên được dùng để đại diện cho **Ý định nghiệp vụ rõ ràng** của người dùng, không dùng để điều khiển kỹ thuật.

### 1. Kích hoạt luồng mới (Entry Points)
Dùng intent để đưa user từ trạng thái `IDLE` vào một chuyên môn cụ thể.
- `INTENT_SEARCH_PRODUCT` -> Chuyển sang `CATALOG_SEARCHING`
- `INTENT_CHECK_LOAN` -> Chuyển sang `FINANCIAL_ANALYZING`

### 2. Cung cấp dữ liệu (Slot Filling)
Dùng intent để xác định user đang cung cấp thông tin cho một "Slot" cụ thể.
- `INTENT_PROVIDE_PHONE` -> Kích hoạt ghi đè slot `customer_phone`.
- `INTENT_CHOOSE_PRODUCT` -> Kích hoạt ghi đè slot `product_id`.

### 3. Ngắt luồng hoặc Quay lại (Control Flow)
Dùng intent để thoát khỏi trạng thái hiện tại một cách có kiểm soát.
- `INTENT_CANCEL` -> Reset về `IDLE`.
- `INTENT_ASK_HUMAN` -> Chuyển sang `HUMAN_HANDOVER`.

---

## ❌ CÁC MẪU CHỐNG CHỈ ĐỊNH (ANTI-PATTERNS)

### 1. Intent nhảy bước (Forbidden Jumps)
Không tạo intent để nhảy cóc qua các bước kiểm tra logic nền tảng.
- *Sai:* `INTENT_FORCE_CHECKOUT` (Trong khi chưa có hàng trong giỏ).
- *Đúng:* User nói "Thanh toán đi", LLM trả về `INTENT_REQUEST_PAYMENT`, nhưng `FlowDecisionService` sẽ chặn nếu state hiện tại không phải là `ORDER_CONFIRMING`.

### 2. Intent đại diện cho Tool (Tool-Intents)
Không đặt tên intent trùng với tên Function/Tool.
- *Sai:* `INTENT_CALL_GET_GOLD_PRICE`.
- *Đúng:* `INTENT_INQUIRY_MARKET_DATA`. (LLM không cần biết nó gọi tool gì, nó chỉ biết user muốn xem giá thị trường).

### 3. Intent chồng chéo (Overlapping)
Tránh các intent quá chung chung khiến LLM bị nhầm lẫn.
- *Sai:* `INTENT_GIVE_INFO` (Quá chung).
- *Đúng:* `INTENT_SUBMIT_HOS_SO`, `INTENT_CONFIRM_ADDRESS`.

---

## 🛠️ QUY TRÌNH THÊM INTENT MỚI

Nếu bạn cần thêm intent mới vào hệ thống:

1.  **Khai báo Enum:** Thêm vào `app/core/domain/runtime.py` -> `class Intent`.
2.  **Cập nhật Flow Matrix:** Khai báo các transition hợp lệ trong `FlowDecisionService` (hoặc DB table tương ứng).
3.  **Training/Prompting:** Cập nhật System Prompt của Agent để LLM nhận diện được intent mới.
4.  **Handler:** Viết logic xử lý kết quả của intent trong `StateHandler`.

---

## 📊 DANH SÁCH INTENT TIÊU CHUẨN (CORE)

| Intent ID | Miêu tả | Ví dụ User nói |
| :--- | :--- | :--- |
| `GREETING` | Chào hỏi ban đầu | "Hi", "Chào bạn" |
| `SEARCH_PRODUCT` | Tìm kiếm sản phẩm | "Cho xem iPhone 17", "Có xe Vios ko?" |
| `INQUIRY_PRICE` | Hỏi giá/khuyến mãi | "Bán bao nhiêu?", "Có giảm giá ko?" |
| `CHECK_AVAILABILITY` | Kiểm tra tồn kho | "Còn hàng ở HN ko?", "Màu đỏ còn ko?" |
| `PROVIDE_INFO` | Cung cấp thông tin slot | "Số điện thoại tôi là 09xx", "Tôi ở TP.HCM" |
| `CONFIRM` | Đồng ý/Xác nhận | "Đúng rồi", "Ok chốt đi" |
| `CANCEL` | Hủy bỏ/Dừng | "Thôi không mua nữa", "Hủy đi" |

---
*Cập nhật lần cuối: 15/02/2026 bởi System Architect.*
