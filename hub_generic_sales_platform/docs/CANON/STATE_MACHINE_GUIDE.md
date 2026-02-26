# Hướng Dẫn Cỗ Máy Trạng Thái (State Machine Guide)

## Tổng Quan

**Cỗ máy trạng thái (State Machine)** là thành phần cốt lõi của Agentic Sales Platform. Nó điều khiển hành vi của Bot bằng cách **giới hạn danh sách Tool** Bot được phép gọi dựa trên giai đoạn hội thoại hiện tại. Nhờ đó, hành trình khách hàng được dẫn dắt có chủ đích, tránh thao tác sai quy cách và tối ưu chi phí token.

### Triết Lý Cốt Lõi

> **Trạng thái định nghĩa phạm vi; Agent thực thi trong phạm vi đó.**

Agent mạnh nhưng bị kiềm chế - nó được phép suy luận tự do nhưng chỉ có quyền gọi những Tool nằm trong whitelist của trạng thái hiện tại.

---

## Các Trạng Thái Vòng Đời (Lifecycle States)

Hệ thống định nghĩa **13 trạng thái vòng đời** đại diện cho các giai đoạn khác nhau trong hành trình khách hàng.

**Nguồn chân lý duy nhất**: `app/core/domain/runtime.py`

```python
class LifecycleState(str, Enum):
    IDLE = "idle"           # Chờ/Nhàn rỗi
    BROWSING = "browsing"   # Duyệt chung
    SEARCHING = "searching" # Đang tìm kiếm tích cực
    FILTERING = "filtering" # Thu hẹp/lọc kết quả
    VIEWING = "viewing"     # Xem chi tiết
    COMPARING = "comparing" # So sánh sản phẩm
    ANALYZING = "analyzing" # Phân tích chuyên sâu
    PURCHASING = "purchasing" # Chốt đơn
    COMPLETED = "completed"  # Phiên hoàn tất thành công
    CLOSED = "closed"       # Kết thúc phiên
    HANDOVER = "handover"   # Nhân viên đã tiếp quản
    ERROR = "error"         # Lỗi xử lý
    WAITING_INPUT = "waiting_input"  # Đợi thông tin từ khách
```

### Mô Tả Trạng Thái

| Trạng thái | Mục đích | Ví dụ ý định khách |
|------------|----------|---------------------|
| **IDLE** | Chờ đợi, tán gẫu | "Chào", " Xin chào" |
| **BROWSING** | Duyệt chung | "Cho tôi xem sản phẩm" |
| **SEARCHING** | Tìm kiếm tích cực | "Tìm laptop dưới 20 triệu" |
| **FILTERING** | Lọc kết quả | "Chỉ hiện màu đỏ thôi" |
| **VIEWING** | Xem chi tiết | "Xem cái thứ 2", "Chi tiết hơn" |
| **COMPARING** | So sánh cạnh nhau | "So sánh 2 cái" |
| **ANALYZING** | Phân tích sâu | "Tính vay giúp tôi" (Tài chính), "Định giá xe cũ" (Ô tô) |
| **PURCHASING** | Chốt đơn | "Đặt hàng", "Đặt lịch xem nhà" |
| **COMPLETED** | Phiên kết thúc thành công | Sau khi mua/đặt thành công |
| **CLOSED** | Phiên đóng | Kết thúc rõ ràng hoặc timeout |
| **HANDOVER** | Nhân viên tiếp quản | Chuyển sang hỗ trợ con người |
| **ERROR** | Lỗi xử lý | Phục hồi sau lỗi hệ thống/tool |
| **WAITING_INPUT** | Đợi khách trả lời | Bot đã hỏi, đang chờ phản hồi |

=> **Điểm linh hoạt ăn tiền:** Mỗi trạng thái có một **whitelist Tool** riêng. Ví dụ khi đang ở `BROWSING`, Bot chỉ được gọi `search_offerings`, `get_offering_details`. Khi sang `ANALYZING`, Bot mới được phép gọi `credit_scoring()` hay `trade_in_valuation`. Nhờ vậy Agent không "ngu" – không thể vừa chào buổi sáng đã đòi lấy lương để chốt gói vay.

---

## Giới Hạn Tool Theo Trạng Thái (STATE_SKILL_MAP)

Mỗi trạng thái định nghĩa **danh sách Tool được phép**. Bot không gọi được Tool nằm ngoài danh sách.

**Triển khai**: `app/core/domain/state_machine.py`

```python
# Ví dụ minh họa - chi tiết đầy đủ trong state_machine.py
STATE_SKILL_MAP: Dict[LifecycleState, Set[str]] = {
    LifecycleState.IDLE: {"search_offerings", "compare_offerings", "get_offering_details", ...},
    LifecycleState.BROWSING: {"search_offerings", "get_offering_details", ...},
    LifecycleState.SEARCHING: {"search_offerings", "get_offering_details", ...},
    LifecycleState.FILTERING: {"search_offerings", "get_offering_details"},
    LifecycleState.VIEWING: {"get_offering_details", "compare_offerings", ...},
    LifecycleState.COMPARING: {"compare_offerings", "get_offering_details", "trigger_web_hook"},
    LifecycleState.ANALYZING: {"get_market_data", "credit_scoring", "trade_in_valuation", ...},
    LifecycleState.PURCHASING: {"trigger_web_hook", "search_offerings", "get_offering_details"},
    # COMPLETED, CLOSED, ERROR, WAITING_INPUT: whitelist hạn chế để phục hồi/chuyển phiên
}
```

### Phân Loại Tool Theo Ngành

| Nhóm | Tool | Ngành áp dụng |
|------|------|---------------|
| **Catalog** | `search_offerings`, `get_offering_details`, `compare_offerings` | Mọi ngành |
| **Tài chính** | `get_market_data`, `get_strategic_analysis`, `credit_scoring` | Vay, Đầu tư |
| **Ô tô** | `trade_in_valuation` | Mua bán xe |
| **Giáo dục** | `assessment_test` | Khóa học, placement |
| **Tích hợp** | `trigger_web_hook` | CRM, PMS, thanh toán |

---

## Chuyển Trạng Thái (State Transitions)

### Trạng thái thay đổi khi nào?

Trạng thái thay đổi thông qua **kết quả thực thi Tool**:

```python
# Tool handler trả về new_state
return {
    "success": True,
    "response": "Tìm được 5 laptop phù hợp",
    "new_state": LifecycleState.BROWSING,
    "results": [...]
}
```

**HybridOrchestrator** đọc `new_state` và cập nhật phiên:

```python
if "new_state" in tool_result:
    await session_handler.update_lifecycle_state(session_id, tool_result["new_state"], tenant_id)
```

### Các Chuyển Đổi Hợp Lệ

Định nghĩa trong `VALID_TRANSITIONS` (state_machine.py). Ví dụ:

| Từ | Đến | Kích hoạt |
|----|-----|-----------|
| IDLE | BROWSING, SEARCHING, ANALYZING | Khách bắt đầu khám phá |
| BROWSING | VIEWING, SEARCHING, FILTERING | Chọn sản phẩm cụ thể / lọc |
| VIEWING | COMPARING, PURCHASING | So sánh hoặc mua |
| COMPARING | VIEWING, PURCHASING | Chọn 1 cái hoặc chốt |
| ANALYZING | VIEWING, PURCHASING | Phân tích xong, bước tiếp |
| PURCHASING | COMPLETED, CLOSED, ERROR | Giao dịch xong / lỗi |
| Bất kỳ | IDLE | Khách đổi chủ đề |

---

## Luồng Xử Lý (Processing Flow)

### 1. Tin nhắn tới

```python
# HybridOrchestrator nhận message
message = "Xem cái thứ 2"
session = get_session(session_id)
current_state = session.lifecycle_state  # Ví dụ: "browsing"
```

### 2. State Machine Lọc Tool

```python
# Chỉ trả về Tool được phép
allowed_tools = StateMachine.get_allowed_tools(current_state)
# Ví dụ: ["get_offering_details", "search_offerings", ...]
```

### 3. Agent Suy Luận (Trong Phạm Vi)

```python
# AgentOrchestrator chỉ gửi allowed_tools cho LLM
llm_result = await llm_provider.generate_response(
    system_prompt="Bạn là trợ lý bán hàng...",
    user_message=message,
    tools=allowed_tools,  # ← BỊ GIỚI HẠN, không phải tất cả
    messages_history=history
)
```

### 4. Cập Nhật Trạng Thái

```python
# Kết quả Tool trả về new_state
tool_result = await execute_tool(tool_name, arguments)
if tool_result.get("new_state"):
    await update_session_state(session_id, tool_result["new_state"])
```

---

## Lợi Ích Của State Machine

### 1. Dự đoán được hành vi

Admin biết rõ Bot được phép và không được phép làm gì ở từng trạng thái.
- Không mua trước khi xem chi tiết
- Không so sánh khi chưa có kết quả tìm kiếm

### 2. Tối ưu Token

Thay vì gửi cả 20+ Tool cho LLM, mỗi trạng thái chỉ cần 4–7 Tool. **Tiết kiệm ~50–70% token** cho tool schema.

### 3. Phân Tích & Theo Dõi

Dashboard hiển thị:
- Khách rời bỏ ở đâu (vd: 60% bỏ ở VIEWING)
- Thời gian trung bình mỗi trạng thái
- Phễu chuyển đổi theo trạng thái

### 4. Guardrails

Nếu LLM "ảo tưởng" gọi Tool không có trong whitelist:

```python
if tool_name not in allowed_tools:
    return {"error": "Tool không được phép ở trạng thái hiện tại"}
```

---

## Ví Dụ Hành Trình Khách Hàng

### Luồng Bán Lẻ (Giày dép, Điện tử)

```
Khách: "Cho tôi xem laptop"
→ Trạng thái: IDLE → BROWSING
→ Tool: search_offerings
→ Kết quả: Hiện 5 laptop

Khách: "Cái thứ 2"
→ Trạng thái: BROWSING → VIEWING
→ Tool: get_offering_details
→ Kết quả: Chi tiết đầy đủ

Khách: "So sánh với cái 4"
→ Trạng thái: VIEWING → COMPARING
→ Tool: compare_offerings
→ Kết quả: Bảng so sánh

Khách: "Mua cái đầu"
→ Trạng thái: COMPARING → PURCHASING
→ Tool: trigger_web_hook
→ Kết quả: Chuyển checkout
```

### Luồng Bất Động Sản / Tài Chính

```
Khách: "Tìm căn 3PN ở Quận 1"
→ Trạng thái: IDLE → BROWSING
→ Tool: search_offerings
→ Kết quả: 3 căn hiện ra

Khách: "Căn đầu hướng nào?"
→ Trạng thái: BROWSING → VIEWING
→ Tool: get_offering_details
→ Kết quả: Chi tiết + hướng nhà

Khách: "Tính vay giúp tôi"
→ Trạng thái: VIEWING → ANALYZING
→ Tool: credit_scoring / get_market_data (tính vay)
→ Kết quả: Bảng trả góp

Khách: "Đặt lịch xem nhà"
→ Trạng thái: ANALYZING → PURCHASING
→ Tool: trigger_web_hook
→ Kết quả: Link đặt lịch gửi khách
```

=> **Điểm linh hoạt ăn tiền:** Luồng Bán lẻ có thể nhảy vọt BROWSING → PURCHASING (mua luôn). Luồng Tài chính phải đứng lâu ở ANALYZING rồi mới sang VIEWING/PURCHASING. Cùng một State Machine, khác flow_config theo ngành.

---

## Thêm Trạng Thái Mới

### Bước 1: Định nghĩa trong Domain

**File**: `app/core/domain/runtime.py`

```python
class LifecycleState(str, Enum):
    # ... trạng thái hiện có
    NEGOTIATING = "negotiating"  # MỚI
```

### Bước 2: Cấu hình State Machine

**File**: `app/core/domain/state_machine.py`

```python
STATE_SKILL_MAP: Dict[LifecycleState, Set[str]] = {
    # ...
    LifecycleState.NEGOTIATING: {"get_offering_details", "submit_counter_offer"}
}
VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
    # Thêm transition đến/từ NEGOTIATING
}
```

### Bước 3: Cập Nhật Tool Handler

Tool trả về `new_state: LifecycleState.NEGOTIATING` khi cần.

### Bước 4: Migration DB (nếu cần)

Nếu DB dùng enum:
```sql
ALTER TYPE lifecycle_state_enum ADD VALUE 'negotiating';
```

---

## Hiện Trạng Triển Khai

### ✅ Đã Có

- 13 trạng thái vòng đời (`app/core/domain/runtime.py`)
- Giới hạn Tool theo trạng thái (`STATE_SKILL_MAP`)
- Quy tắc chuyển trạng thái (`VALID_TRANSITIONS`)
- Lưu trạng thái trong DB
- Phục hồi lỗi: trạng thái `ERROR`, `WAITING_INPUT`
- Luồng tiếp quản: trạng thái `HANDOVER`

### ⚠️ Có Thể Cải Thiện

- **Strict transition**: Hiện cho phép linh hoạt; có thể siết chặt nếu cần
- **State timeout**: Phiên chưa tự hết hạn khi idle lâu
- **Dashboard phân tích**: Đã có nhưng có thể chi tiết hơn

---

## Gợi Ý Thực Hành

**Nên:**
- Luôn giới hạn Tool theo trạng thái
- Trả về `new_state` từ tool handler khi cần đổi trạng thái
- Ghi log chuyển trạng thái để phân tích
- Đặt tên trạng thái dạng hiện tại phân từ (BROWSING, VIEWING)

**Không nên:**
- Vượt qua State Machine (gọi Tool trực tiếp)
- Tạo quá nhiều trạng thái (tool vỡ vụn)
- Hard-code transition (dùng config khai báo)
- Quên cập nhật hiển thị trạng thái ở Frontend

---

**Trạng thái Tài liệu**: Phản ánh triển khai hiện tại.
**Cập nhật lần cuối**: Tháng 02/2026.
**Vị trí**: `app/core/domain/state_machine.py`
