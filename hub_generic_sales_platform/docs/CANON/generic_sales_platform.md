# Generic Sales Platform: Offering-Centric Architecture

## Overview

**Agentic Sales Platform** không chỉ là một chatbot bán hàng. Đây là một **Generic Sales Platform** được thiết kế để hỗ trợ bất kỳ quy trình chuyển đổi (conversion) nào - từ bán lẻ (retail) đến dịch vụ cao cấp (high-ticket services).

### Core Philosophy

> **DATA + CONVERSATION = CONVERSION**

Thay vì giới hạn ở mô hình E-commerce truyền thống (Product → Cart → Checkout), hệ thống sử dụng mô hình **Offering-centric** linh hoạt hơn để phục vụ đa ngành.

---

## Why "Generic"?

### Traditional E-commerce Limitation

Platforms như Shopify, WooCommerce chỉ tối ưu cho **retail**:
- Fixed schema: SKU, Inventory, Shipping
- Linear flow: Browse → Add to Cart → Checkout
- Static pricing
- Physical products only

### Generic Sales Platform Advantage

Hỗ trợ **mọi loại offering**:
- **Physical Products**: Quần áo, điện tử (như E-commerce)
- **Services**: Khóa học, tư vấn, dịch vụ spa
- **Assets**: Bất động sản, ô tô
- **Financial Products**: Gói vay, bảo hiểm

---

## Key Abstractions

### 1. From "Product" to "Offering"

**Traditional Product Model**:
```python
class Product:
    sku: str          # Only for physical goods
    inventory: int    # Doesn't apply to services
    weight: float     # Irrelevant for digital/financial
```

**Offering Model** (Current Implementation):
```python
class TenantOffering:
    offering_type: str  # "product" | "service" | "asset" | "financial"
    bot_id: Optional[str]  # Can be tied to specific bot
    base_attributes: Dict  # Flexible JSONB
    
class OfferingVersion:
    attributes: Dict  # Dynamic attributes based on domain
    pricing_rules: Dict  # Complex pricing logic
```

**Examples**:

| Offering Type | Attributes Example |
|---------------|-------------------|
| **Physical (Laptop)** | `{brand, model, ram, storage, warranty}` |
| **Service (Khóa học)** | `{instructor, duration, level, schedule}` |
| **Asset (Nhà)** | `{area, bedrooms, direction, legal_status}` |
| **Financial (Vay)** | `{interest_rate, term, min_income, max_ltv}` |

### 2. From "Cart" to "Context Slots"

**Traditional Cart**:
- Items with quantity
- One-size-fits-all

**Context Slots** (Current Implementation):
```python
class RuntimeContextSlot:
    slot_key: str      # "budget", "color", "location"
    slot_value: str    # "5-7 tỷ", "đỏ", "Quận 1"
    confidence: float  # AI extraction confidence
    expires_at: datetime  # TTL for relevance
```

**Use Cases**:

| Domain | Context Slots |
|--------|---------------|
| **Retail** | color, size, brand_preference |
| **Real Estate** | budget, location, bedrooms, direction |
| **Auto** | make, model, year, max_price |
| **Education** | current_level, goal, schedule_preference |
| **Finance** | income, credit_score, loan_purpose |

### 3. From "Checkout" to "Dynamic Flow"

**Traditional Checkout Flow**:
```
View Product → Add to Cart → Fill Shipping → Payment → Done
```

**Dynamic Lifecycle States** (Current Implementation):
```python
class LifecycleState(str, Enum):
    IDLE = "idle"
    BROWSING = "browsing"
    VIEWING = "viewing"
    COMPARING = "comparing"
    ANALYZING = "analyzing"  # For financial/market analysis
    PURCHASING = "purchasing"
    CLOSED = "closed"
```

**Domain-Specific Flows**:

**Retail**:
```
IDLE → BROWSING (search) → VIEWING (details) → PURCHASING (checkout)
```

**Real Estate**:
```
IDLE → BROWSING (search properties) → VIEWING (details) 
     → ANALYZING (mortgage calculation) → PURCHASING (schedule visit)
```

**Finance**:
```
IDLE → ANALYZING (credit check) → VIEWING (loan options) 
     → PURCHASING (submit application)
```

**Education**:
```
IDLE → BROWSING (course catalog) → VIEWING (course details) 
     → ANALYZING (placement test) → PURCHASING (enrollment)
```

---

## Implementation in Current System

### 1. Database Schema

**Offering Table**:
```sql
CREATE TABLE tenant_offering (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    bot_id UUID,  -- NEW: Can scope offering to specific bot
    code VARCHAR(100) UNIQUE,
    offering_type VARCHAR(50),
    base_attributes JSONB  -- Flexible structure
);
```

**Domain-Agnostic Attributes**:
```sql
CREATE TABLE offering_attribute_value (
    offering_id UUID,
    attribute_key VARCHAR(100),  -- "bedrooms", "interest_rate", etc.
    attribute_value TEXT,
    attribute_type VARCHAR(50)   -- "string", "number", "range"
);
```

### 2. Tool System

Tools are **domain-aware** but use generic operations:

**Generic Tools** (work for all domains):
- `search_offerings(query)` - Semantic search
- `get_offering_details(offering_id)` - Get full details
- `compare_offerings(offering_ids)` - Side-by-side comparison

**Domain-Specific Tools**:
- **Financial**: `get_market_data()`, `credit_scoring()`
- **Auto**: `trade_in_valuation(make, model, year)`
- **Education**: `assessment_test(subject)`
- **Integration**: `trigger_web_hook(action)` - Connect to external CRM/PMS

### 3. Customization Points

**Per-Domain Configuration**:

```python
# In TenantDomain table
domain_config = {
    "ontology": {
        "attributes": ["bedrooms", "area", "direction", "price"],
        "required": ["bedrooms", "price"],
        "facets": ["location", "price_range"]
    },
    "flow_config": {
        "default_state": "idle",
        "allows_comparison": True,
        "requires_analysis": True  # Enable mortgage calculator
    },
    "pricing_rules": {
        "type": "negotiable",  # vs "fixed"
        "show_range": True
    }
}
```

---

## Target Markets

### 1. High-Ticket Sales (SME)

**Industries**:
- Bất động sản (Real Estate)
- Ô tô (Automotive)
- Bảo hiểm (Insurance)
- Giáo dục cao cấp (Premium Education)
- Thẩm mỹ viện (Medical Spa)

**Pain Points**:
- Shopify/WooCommerce không phù hợp (không có "Đặt lịch tư vấn")
- Cần qualify leads 24/7
- Flow phức tạp: Chat → Appointment → Site Visit → Contract

**Why They Pay**:
- 1 Lead = vài triệu → vài trăm triệu VND
- Automation tăng conversion rate = ROI cao
- Generic platform = không cần custom development

### 2. Multi-Channel Chains (Enterprise)

**Industries**:
- Chuỗi F&B (Coffee chains, Restaurants)
- Chuỗi bán lẻ (Fashion, Pharmacy)

**Pain Points**:
- Cần quản lý tập trung (Omnichannel)
- Muốn sở hữu data (không phụ thuộc marketplace)
- Inventory sync across channels

**Why They Pay**:
- Multi-tenant architecture
- Unified view: Web + Zalo + Facebook
- Data ownership

### 3. Agencies (Whitelabel Partners)

**Target**:
- Marketing agencies
- Software houses

**Business Model**:
- Thuê platform core từ chúng ta
- Config cho từng client (e.g., Lan Đột Biến shop, Gara ô tô)
- Bán như giải pháp custom

**Why They Pay**:
- Outsource core AI engine
- Focus on vertical domain expertise
- Faster time-to-market

---

## Example Scenarios

### Retail (Traditional E-commerce)

**User**: "Tôi muốn mua laptop cho design"

**Flow**:
1. `search_offerings(query="laptop design")` → List offerings
2. User: "Cái thứ 2"
3. `get_offering_details(offering_id=...)` → Show specs
4. User: "Có màu xám không?"
5. Check variants → "Có, giá 25tr"
6. User: "Đặt luôn"
7. State → PURCHASING → Trigger webhook to payment gateway

### Real Estate

**User**: "Tôi cần căn 3PN ở Quận 1, ngân sách 7 tỷ"

**Context Extraction**:
- `bedrooms = 3`
- `location = Quận 1`
- `budget = 7000000000`

**Flow**:
1. `search_offerings(query="căn hộ", bedrooms=3, location="Quận 1")` → 5 results
2. User: "Căn đầu tiên view như thế nào?"
3. `get_offering_details(id=...)` → Show images, direction, legal status
4. User: "Tính vay giúp tôi"
5. State → ANALYZING → `get_market_data()` → Show mortgage calculation
6. User: "Đặt lịch xem nhà"
7. `trigger_web_hook(action="schedule_visit")` → CRM integration

### Finance (Loan Application)

**User**: "Tôi muốn vay 100 triệu"

**Flow**:
1. Extract context: `loan_amount = 100000000`
2. State → ANALYZING → `credit_scoring()` → Check eligibility
3. `search_offerings(type="loan", amount=100tr)` → Show loan packages
4. User: "Gói lãi suất 8%/năm"
5. `get_offering_details(id=...)` → Show terms, requirements
6. User: "Nộp hồ sơ luôn"
7. `trigger_web_hook(action="submit_application")` → Bank API integration

### Education (Course Enrollment)

**User**: "Con tôi học lớp 5, muốn học tiếng Anh"

**Flow**:
1. Extract: `grade = 5`, `subject = English`
2. State → ANALYZING → `assessment_test(subject="English")` → Online test
3. Test result → "Con bạn ở level Pre-Intermediate"
4. `search_offerings(level="Pre-Int", grade=5)` → Show courses
5. User: "Khóa thứ 2 học buổi nào?"
6. `get_offering_details(id=...)` → Schedule, instructor, syllabus
7. User: "Đăng ký thử 1 buổi"
8. State → PURCHASING → `trigger_web_hook(action="trial_booking")`

---

## Technical Benefits

### 1. No Code Changes for New Domains

**Adding a new domain** (e.g., Travel Tours):
1. Create `TenantDomain` with ontology config
2. Define attributes in `DomainAttribute` table
3. Upload offerings via Migration Hub
4. **Done** - No backend code changes needed

### 2. Extensibility via Tools

New domain needs special logic? Add new tool:
```python
@agent_tools.register_tool(
    name="calculate_tour_feasibility",
    capability="tour_planning"
)
async def calculate_tour_feasibility(
    destination: str, 
    group_size: int,
    **kwargs
):
    # Domain-specific logic
    return {...}
```

### 3. Unified Analytics

All domains share same metrics:
- Conversation → Conversion rate
- Average handling time
- Token cost per session
- Revenue per session

---

## Future Enhancements

1. **Auto-Ontology Extraction**: AI analyzes competitor websites → auto-generate domain config
2. **Dynamic Pricing Engine**: ML-based price optimization per channel
3. **Multi-Language Support**: Same offering, different languages
4. **Marketplace Mode**: Allow multiple tenants to list offerings in shared catalog

---

**Document Status**: Reflects current implementation  
**Last Updated**: February 2026

**Related Docs**:
- [Scenarios: Real Estate](scenariosigh_ticket_real_estate.md)
- [Scenarios: Finance](scenariosinance_unsecured_loan.md)
- [Scenarios: Education](scenariosducation_admissions.md)
- [Scenarios: Auto Sales](scenariossed_car_sales.md)