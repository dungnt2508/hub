# Nền Tảng Bán Hàng Đa Năng (Generic Sales Platform): Kiến trúc Lấy Sản Phẩm Làm Trung Tâm (Offering-Centric)

## Tổng Quan

**Agentic Sales Platform** không chỉ là một con chatbot bán hàng thông thường. Đây là một **Nền tảng Bán hàng Đa năng (Generic Sales Platform)** được thiết kế linh hoạt để hỗ trợ bất kỳ quy trình chuyển đổi (conversion) nào - từ bán lẻ (retail) đơn giản cho đến các dịch vụ giá trị cao (high-ticket services).

### Triết Lý Cốt Lõi

> **DỮ LIỆU (DATA) + HỘI THOẠI (CONVERSATION) = CHUYỂN ĐỔI (CONVERSION)**

Thay vì bị giới hạn trong mô hình Thương mại điện tử (E-commerce) truyền thống chỉ biết (Sản phẩm → Thêm vào giỏ → Thanh toán), hệ thống áp dụng mô hình lấy **Đề nghị/Sản phẩm làm trung tâm (Offering-centric)** cực kỳ linh hoạt để phục vụ đa ngành nghề.

---

## Tại sao lại gọi là "Đa Năng (Generic)"?

### Hạn chế của E-commerce truyền thống

Các nền tảng như Shopify, WooCommerce chỉ tối ưu cho việc **bán lẻ**:
- Cấu trúc cố định (Fixed schema): Luôn phải có mã SKU, Tồn kho (Inventory), Phí vận chuyển (Shipping).
- Luồng đi tuyến tính: Xem hàng → Bỏ giỏ hàng → Thanh toán.
- Giá cả cố định.
- Chỉ bán được hàng hóa vật lý.

### Lợi thế của Generic Sales Platform

Hỗ trợ **mọi loại hình sản phẩm (offering)**:
- **Physical Products (Hàng vật lý)**: Quần áo, đồ điện tử (giống E-commerce).
- **Services (Dịch vụ)**: Khóa học, tư vấn tài chính, dịch vụ spa làm đẹp.
- **Assets (Tài sản lớn)**: Bất động sản, ô tô.
- **Financial Products (Tài chính)**: Gói vay tín chấp, mua bảo hiểm.

---

## Các Tầng Trừu Tượng Hóa Tạo Nên Sự Linh Hoạt (Key Abstractions)

### 1. Phá bỏ quan niệm "Sản phẩm" truyền thống bằng mô hình `Offering`

**Cách thiết kế CŨ (Sẽ bị chết cứng nếu mang đi bán khóa học hay cho vay tiền):**
```python
class Product:
    sku: str          # Phải có mã SKU (Vô nghĩa với dịch vụ)
    inventory: int    # Phải có tồn kho (Không áp dụng cho bán Khóa học online)
    weight: float     # Trọng lượng (Vô nghĩa với Hợp đồng tài chính)
```

**Cách thiết kế MỚI (Của hệ thống hiện tại):**
```python
class TenantOffering:
    offering_type: str  # Phân loại: "product" | "service" | "asset" | "financial"
    base_attributes: Dict  # Flexible JSONB (Chứa bất cứ thuộc tính nào tùy ngành)
    
class OfferingVersion:
    attributes: Dict  # Thuộc tính động theo từng ngành (Domain)
    pricing_rules: Dict  # Logic tính giá phức tạp
```

=> **Điểm linh hoạt ăn tiền:** Hệ thống không quan tâm khách hàng đang bàn về "Cái áo" hay "Hợp đồng Vay 1 tỷ". Bản chất nó đều là một **"Đề nghị (Offering)"** có các **"Thuộc tính (Attributes)"** đi kèm. Vì thế, chỉ việc nạp bộ cấu hình Data (Ontology) mới vào là con Bot sẽ tự hiểu sản phẩm mới mà hoàn toàn không cần sửa Code DB hay file Entity backend.

**Ví dụ:**

| Loại Offering | Ví dụ Thuộc Tính (Attributes) |
|---------------|-------------------|
| **Vật lý (Laptop)** | `{brand, model, ram, storage, warranty}` |
| **Dịch vụ (Khóa học)** | `{instructor, duration, level, schedule}` |
| **Tài sản (Nhà ở)** | `{area, bedrooms, direction, legal_status}` |
| **Tài chính (Gói vay)** | `{interest_rate, term, min_income, max_ltv}` |

### 2. Trừu tượng hóa "Giỏ hàng" thành `Context Slots`

Thường các web E-comerce dùng giỏ hàng (Cart -> Checkout). Điều này rất vô nghĩa với Ngành Bất Động Sản hay Tài chính vì khách không "bỏ cái nhà vào giỏ hàng rồi bấm thanh toán". Thay vào đó, hệ thống lưu mọi thông tin khách hàng cung cấp dưới dạng `RuntimeContextSlot`:

**Cấu trúc Context Slots** (khớp `runtime_context_slot`):
```python
class RuntimeContextSlot:
    key: str           # "màu sắc", "diện tích", "lương tháng"
    value: str         # "Đỏ", "70m2", "Kỹ sư phần mềm"
    status: str        # active, overridden, conflict, inferred
    source: str        # user, system, inferred
    source_turn_id: str  # Turn trích xuất ra slot này
# Ghi chú: confidence, expires_at — kế hoạch mở rộng
```

=> **Điểm linh hoạt ăn tiền:** `ContextSlots` hoạt động giống "Trí nhớ ngắn hạn" của con người. Bot cứ tự nhiên túc tắc hỏi chuyện, thu thập các "Slot" (mảnh ghép thông tin) này rồi nhét vào System Prompt của LLM. LLM sẽ nhìn vào các mảnh ghép (Slots) đã gom đủ chưa để ra quyết định xem đã gọi Tool được chưa hay cần chuyển trạng thái (State). Nhờ cái "Trí nhớ" đa năng này, bạn có thể xây tới 100 kịch bản bán hàng (Scenarios) khác nhau dễ dàng.

**Ví dụ thực tế:**

| Ngành (Domain) | Context Slots (Ngữ cảnh cần lấy) |
|--------|---------------|
| **Bán lẻ** | color (màu sắc), size (kích cỡ), brand_preference (thương hiệu) |
| **Bất động sản** | budget (ngân sách), location (địa điểm), bedrooms (số phòng ngủ) |
| **Ô tô** | make (hãng), model (dòng xe), year (đời xe), max_price (giá tối đa) |
| **Giáo dục** | current_level (trình độ), goal (mục tiêu), schedule_preference (lịch học rảnh) |
| **Tài chính** | income (lương), credit_score (điểm tín dụng), loan_purpose (mục đích vay) |

### 3. Vòng đời giao dịch vạn năng (Lifecycle State Machine)

Kịch bản Bán Hàng giờ đây được biến thành một Cỗ máy trạng thái (StateMachine): `IDLE` -> `BROWSING` -> `VIEWING` -> `COMPARING` -> `ANALYZING` -> `PURCHASING`.

*   **Bán Rẻ đắt (Giày dép):** Đi thẳng từ `BROWSING` (Tư vấn size) nhảy vọt qua `PURCHASING` (Mua luôn). Bỏ qua `ANALYZING`.
*   **Bán tỷ đô (Vay ngân hàng):** Bắt đầu `IDLE` -> Đứng rất lâu ở `ANALYZING` (Tính lãi suất trả góp, check nợ xấu) -> Rồi mới sang `VIEWING` (Khuyên dùng Gói 1) -> `PURCHASING` (Chốt sales tạo hồ sơ).

**Các Trạng thái Động (Dynamic Lifecycle States)**:

> **Nguồn chân lý duy nhất**: `app/core/domain/runtime.py`

```python
class LifecycleState(str, Enum):
    IDLE = "idle"           # Chờ/Nhàn rỗi
    BROWSING = "browsing"   # Duyệt chung (tương tác tìm kiếm)
    SEARCHING = "searching" # Đang tìm kiếm tích cực
    FILTERING = "filtering" # Thu hẹp/lọc kết quả
    VIEWING = "viewing"     # Bấm xem thông tin chi tiết
    COMPARING = "comparing" # So sánh sản phẩm
    ANALYZING = "analyzing" # Phân tích chuyên sâu (vd: tài chính/thị trường)
    PURCHASING = "purchasing" # Thực hiện lệnh Mua/Chốt đơn
    COMPLETED = "completed"  # Phiên hoàn tất thành công
    CLOSED = "closed"       # Kết thúc phiên
    HANDOVER = "handover"   # Nhân viên con người đã tiếp quản
    ERROR = "error"         # Lỗi xử lý
    WAITING_INPUT = "waiting_input"  # Đợi thông tin từ khách
```

=> **Điểm linh hoạt ăn tiền:** Hệ thống biết cách "Khóa cò" Bot (Guardrails). Ví dụ khi đang ở trạng thái `BROWSING`, Bot chỉ được phép gọi nhóm tool `Search` hoặc `View Details`. Khi chuyển hẳn sang `ANALYZING`, Bot mới được thả cho phép gọi tool `credit_scoring()`. Sự phân luồng State này giúp Agentic không bị "ngu" và hành xử phi logic (Ví dụ: Khách mới vô bảo chào buổi sáng thì nó đòi lấy thông tin thu nhập để chốt gói Vay).

### 4. Gắn kết Tool / Skill Plugin thay vì rập khuôn (Plugin Architecture)

Hệ thống Core (Agentic Reasoning) hoàn toàn không biết ngành nghề kinh doanh là gì. Bạn định hình nghiệp vụ bằng cách cắm thêm các Tool (Kỹ năng).

Nhờ cơ chế Decorator Register Tool (`agent_tool_registry.py`), Agent như một người lính được khoác "Áo giáp" (Skill) linh hoạt:

```python
# Bất cứ khi nào cần nhận làm ngành mới, chỉ cần DEV THÊM 1 HÀM MỚI TÁCH BIỆT:
@agent_tools.register_tool(
    name="calculate_tour_feasibility",
    capability="tour_planning"
)
async def calculate_tour_feasibility(
    destination: str, 
    group_size: int,
    **kwargs
):
    # Logic tính toán của riêng mảng Du Lịch
    return {...}
```

=> **Điểm linh hoạt ăn tiền:** File điều phối trung tâm (`hybrid_orchestrator.py`) hoàn toàn không bị phình to. Khi bạn onboard một khách hàng mới làm mảng Spa làm đẹp, bạn chỉ việc lập trình thêm 1 Tool tên là `check_booking_slot` và "cắm" (Plug) nó vào hệ thống đăng ký là xong. Luồng suy nghĩ của AI (Core Reasoning) không hề suy suyển.

---

**Tóm lại**, hệ thống này CỰC KỲ LINH HOẠT vì nó tuân thủ triệt để nguyên tắc **Tách biệt Dữ liệu (TenantData/Ontology) ra khỏi Phần Trí Tuệ (Core Agentic Reasoning)**. Bạn đang xây một *"Bộ não nhân tạo bán hàng"* đạt chuẩn, chỉ cần cắm chiếc "USB" chứa Dữ liệu của Ngành nào vào, bộ não đó sẽ tự khắc biến thành Chuyên gia của riêng ngành đó mà không cần đập đi xây lại Backend.

---

## Chi tiết Triển Khai Trong Hệ Thống Hiện Tại

### Cơ Sở Dữ Liệu (Database Schema)

**Bảng Product cốt lõi (Offering Table)**:
```sql
CREATE TABLE tenant_offering (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    bot_id UUID,  -- Gán chặt loại "hàng hóa" đó cho Bot nhất định quản lý
    code VARCHAR(100) UNIQUE,
    offering_type VARCHAR(50),  -- 'product', 'service', v.v
    base_attributes JSONB  -- Nhét mọi thông tin động vào đây
);
```

**Bảng Thuộc Tính (Domain-Agnostic Attributes)**:
```sql
CREATE TABLE offering_attribute_value (
    offering_id UUID,
    attribute_key VARCHAR(100),  -- Giá trị như: "bedrooms", "interest_rate"
    attribute_value TEXT,
    attribute_type VARCHAR(50)   -- Định dạng: "string", "number", "range"
);
```

### Điểm Tùy Chỉnh Theo Ngành (Customization Points)

Ví dụ mô phỏng file cấu hình JSON cho một Tenant ngành nghề cụ thể:

```python
# Lưu trong bảng TenantDomain
domain_config = {
    "ontology": {
        "attributes": ["bedrooms", "area", "direction", "price"],
        "required": ["bedrooms", "price"],
        "facets": ["location", "price_range"]
    },
    "flow_config": {
        "default_state": "idle",
        "allows_comparison": True,
        "requires_analysis": True  # Kích hoạt bắt buộc phải qua tính máy tính vay mua nhà
    },
    "pricing_rules": {
        "type": "negotiable",  # Mua nhà thì có thể thương lượng giá (ngược lại với fixed)
        "show_range": True
    }
}
```

---

## Chiến Lược Thương Mại / Khách Hàng Mục Tiêu

### 1. Bán hàng Giá Trị Cao (High-Ticket Sales)
**Ngành**: Bất động sản, Ô tô, Bảo hiểm, Thẩm mỹ viện, Phòng khám.
**Nỗi đau**: Khách cần tư vấn (Qualify) 24/7. Họ không bỏ cái nhà vào giỏ hàng Shopify được. Cần quy trình Chat → Đặt lịch hẹn → Cọc.
**Lý do họ Mua**: Tự động hóa Agentic giúp chốt sale tốt hơn. 1 Lead (đơn) trị giá rất lớn, doanh nghiệp sẵn sàng chịu chi mảng SaaS này.

### 2. Chuỗi Doanh Nghiệp (Multi-Channel Enterprise)
**Ngành**: Chuỗi F&B, Thời trang, Nhượng quyền.
**Nỗi đau**: Muốn giữ data khách hàng, không muốn làm phụ thuộc sàn thương mại điện tử.
**Lý do họ Mua**: Multi-tenant cho phép quản lý tồn kho linh hoạt (Omnichannel) vừa web vừa Zalo trên cùng 1 con bot quản lý tập trung.

### 3. Đối tác Đại lý (Whitelabel Agencies)
**Đối tượng**: Marketing agencies, Software houses.
**Lý do họ Mua**: Họ thuê cái lõi "Generic Backend" này của bạn. Sau đó họ tự về cấu hình config ontology (xe hơi, trái cây, shop thú cưng...) rồi đẩy đi bán tiếp cho khách hàng của họ, làm giảm hẳn chi phí phải thuê team dev viết lại code backend AI.

---
**Trạng thái Tài liệu**: Phản ánh kiến trúc triển khai hiện tại.
**Cập nhật lần cuối**: Tháng 02/2026.