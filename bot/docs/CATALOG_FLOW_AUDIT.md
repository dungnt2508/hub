# Catalog Flow Audit - So sánh Flow Hiện Tại vs Flow Mong Muốn

**Ngày kiểm tra:** 2026-01-16  
**Mục tiêu:** Đánh giá xem flow catalog hiện tại đã đi theo flow mong muốn chưa

---

## 📋 Flow Mong Muốn

```
[User mở chat]
      ↓
[Bot chào + xác định intent]
      ↓
[Nếu muốn xem catalog] → [Hỏi tiêu chí lọc]
      ↓
[Lọc & trả danh sách sản phẩm]
      ↓
[Chọn sản phẩm]
      ↓
[Hiển thị chi tiết sản phẩm]
      ↓
[Thêm vào giỏ hàng]
      ↓
[Thu thập thông tin khách]
      ↓
[Chốt đơn / chuyển livechat]
      ↓
[Theo dõi + chăm sóc sau mua]
```

---

## ✅ Flow Hiện Tại - Đã Implement

### 1. ✅ User mở chat
**Status:** ✅ **ĐÃ CÓ**
- Router orchestrator xử lý request từ user
- Session management với `SessionState`
- Conversation state machine quản lý flow

**Files:**
- `backend/router/orchestrator.py`
- `backend/router/steps/session_step.py`
- `backend/router/conversation_state_machine.py`

---

### 2. ✅ Bot chào + xác định intent
**Status:** ✅ **ĐÃ CÓ**
- Router xác định intent qua multiple sources:
  - PATTERN matching
  - EMBEDDING classification
  - LLM classification
  - CONTINUATION detection
- Meta-task detection (greeting, goodbye, etc.)

**Files:**
- `backend/router/orchestrator.py`
- `backend/router/steps/meta_step.py`
- `backend/router/steps/pattern_step.py`
- `backend/router/steps/embedding_step.py`
- `backend/router/steps/llm_step.py`

**Intents đã có:**
- `search_products` → `catalog.search`
- `query_product_detail` → `catalog.info`
- `search_by_category` → `catalog.search`
- `query_price` → `catalog.price`
- `check_availability` → `catalog.availability`
- `compare_products` → `catalog.compare`

---

### 3. ✅ Hỏi tiêu chí lọc
**Status:** ✅ **ĐÃ CÓ (Partial)**
- `SearchProductUseCase` có optional slots:
  - `question`, `query`, `product_type`, `feature`, `tag`
- Domain có thể return `NEED_MORE_INFO` với `next_action="ASK_SLOT"`
- Session state lưu `missing_slots` và `slots_memory`

**Files:**
- `backend/domain/catalog/use_cases/search_product.py`
- `backend/schemas/domain_types.py` (DomainResponse với next_action)

**Ví dụ:**
```python
# Nếu thiếu query, domain có thể hỏi:
DomainResponse(
    status=DomainResult.NEED_MORE_INFO,
    message="Bạn muốn tìm kiếm sản phẩm theo tiêu chí nào? (loại sản phẩm, tính năng, tag...)",
    next_action="ASK_SLOT",
    next_action_params={"slot_name": "query", "all_missing": ["query"]}
)
```

**⚠️ Thiếu:**
- Chưa có logic tự động hỏi tiêu chí lọc khi user chỉ nói "xem catalog"
- Chưa có guided questions để thu thập filters

---

### 4. ✅ Lọc & trả danh sách sản phẩm
**Status:** ✅ **ĐÃ CÓ**
- `SearchProductUseCase` search products từ catalog API
- Trả về danh sách products với format chuẩn
- Support filtering qua slots (product_type, feature, tag)

**Files:**
- `backend/domain/catalog/use_cases/search_product.py`
- `backend/domain/catalog/adapters/catalog_repository.py`
- `backend/infrastructure/catalog_client.py`

**Response format:**
```python
DomainResponse(
    status=DomainResult.SUCCESS,
    message="Tìm thấy 5 sản phẩm: ...",
    data={
        "products": [...],
        "count": 5
    }
)
```

---

### 5. ✅ Chọn sản phẩm
**Status:** ✅ **ĐÃ CÓ (Partial)**
- User có thể mention product name/ID trong message
- Router extract `product_id` hoặc `product_name` từ slots
- Continuation flow có thể detect product selection từ context

**Files:**
- `backend/router/orchestrator.py` (_step_0_6_continuation)
- `backend/domain/catalog/use_cases/get_product_info.py`

**⚠️ Thiếu:**
- Chưa có interactive product selection (buttons, quick replies)
- Chưa có product list display với clickable items

---

### 6. ✅ Hiển thị chi tiết sản phẩm
**Status:** ✅ **ĐÃ CÓ**
- `GetProductInfoUseCase` lấy chi tiết product từ catalog API
- Trả về đầy đủ thông tin: title, description, price, availability, features

**Files:**
- `backend/domain/catalog/use_cases/get_product_info.py`

**Response format:**
```python
DomainResponse(
    status=DomainResult.SUCCESS,
    message="Thông tin về 'Product Name': Mô tả: ... Giá: ... Tình trạng: ...",
    data={"product": {...}}
)
```

---

## ❌ Flow Hiện Tại - CHƯA Implement

### 7. ❌ Thêm vào giỏ hàng
**Status:** ❌ **CHƯA CÓ**

**Thiếu:**
- Intent: `add_to_cart` hoặc `catalog.cart.add`
- Use case: `AddToCartUseCase`
- Cart management trong session state
- Integration với catalog cart API (nếu có)

**Cần implement:**
```yaml
# intent_registry.yaml
- intent: add_to_cart
  domain: catalog
  intent_type: OPERATION
  required_slots: [product_id, quantity]
  optional_slots: [variant_id]
  source_allowed: [PATTERN, EMBEDDING, LLM]
  use_case_key: catalog.cart.add
```

```python
# backend/domain/catalog/use_cases/add_to_cart.py
class AddToCartUseCase(CatalogUseCase):
    async def execute(self, request: DomainRequest) -> DomainResponse:
        # Add product to cart
        # Store cart in session state or external cart service
        pass
```

---

### 8. ❌ Thu thập thông tin khách
**Status:** ❌ **CHƯA CÓ**

**Thiếu:**
- Intent: `collect_customer_info` hoặc `catalog.checkout.collect_info`
- Use case để collect:
  - Tên, email, phone
  - Địa chỉ giao hàng
  - Payment method
- Form-like conversation flow với slot validation

**Cần implement:**
```yaml
- intent: collect_customer_info
  domain: catalog
  intent_type: OPERATION
  required_slots: [name, email, phone, address]
  optional_slots: [payment_method, notes]
  source_allowed: [PATTERN, LLM]
  use_case_key: catalog.checkout.collect_info
```

```python
# backend/domain/catalog/use_cases/collect_customer_info.py
class CollectCustomerInfoUseCase(CatalogUseCase):
    async def execute(self, request: DomainRequest) -> DomainResponse:
        # Collect customer info step by step
        # Validate format (email, phone)
        # Store in session state
        pass
```

---

### 9. ❌ Chốt đơn / chuyển livechat
**Status:** ❌ **CHƯA CÓ**

**Thiếu:**
- Intent: `place_order` hoặc `catalog.checkout.place_order`
- Intent: `escalate_to_livechat` hoặc `catalog.support.escalate`
- Use case để:
  - Place order với cart items và customer info
  - Escalate to human support khi cần
- Integration với order service

**Cần implement:**
```yaml
- intent: place_order
  domain: catalog
  intent_type: OPERATION
  required_slots: [cart_id, customer_info]
  optional_slots: [payment_method, shipping_method]
  source_allowed: [PATTERN, LLM]
  use_case_key: catalog.checkout.place_order

- intent: escalate_to_livechat
  domain: catalog
  intent_type: OPERATION
  required_slots: []
  optional_slots: [reason, context]
  source_allowed: [PATTERN, LLM, ESCALATION]
  use_case_key: catalog.support.escalate
```

```python
# backend/domain/catalog/use_cases/place_order.py
class PlaceOrderUseCase(CatalogUseCase):
    async def execute(self, request: DomainRequest) -> DomainResponse:
        # Validate cart and customer info
        # Create order via catalog API
        # Return order confirmation
        pass

# backend/domain/catalog/use_cases/escalate_to_livechat.py
class EscalateToLivechatUseCase(CatalogUseCase):
    async def execute(self, request: DomainRequest) -> DomainResponse:
        # Set escalation_flag in session
        # Transfer to livechat service
        # Return handoff message
        pass
```

---

### 10. ❌ Theo dõi + chăm sóc sau mua
**Status:** ❌ **CHƯA CÓ**

**Thiếu:**
- Intent: `track_order` hoặc `catalog.order.track`
- Intent: `post_purchase_care` hoặc `catalog.support.post_purchase`
- Use case để:
  - Track order status
  - Send follow-up messages
  - Handle returns/refunds

**Cần implement:**
```yaml
- intent: track_order
  domain: catalog
  intent_type: KNOWLEDGE
  required_slots: [order_id]
  optional_slots: []
  source_allowed: [PATTERN, EMBEDDING, LLM]
  use_case_key: catalog.order.track

- intent: post_purchase_care
  domain: catalog
  intent_type: OPERATION
  required_slots: []
  optional_slots: [order_id, issue_type]
  source_allowed: [PATTERN, LLM]
  use_case_key: catalog.support.post_purchase
```

---

## 📊 Tổng Kết

| Step | Flow Mong Muốn | Status | Implementation |
|------|----------------|--------|----------------|
| 1 | User mở chat | ✅ | Router orchestrator + Session management |
| 2 | Bot chào + xác định intent | ✅ | Multi-source routing (PATTERN, EMBEDDING, LLM) |
| 3 | Hỏi tiêu chí lọc | ⚠️ Partial | Có slots nhưng chưa có guided questions |
| 4 | Lọc & trả danh sách | ✅ | SearchProductUseCase |
| 5 | Chọn sản phẩm | ⚠️ Partial | Có nhưng chưa có interactive selection |
| 6 | Hiển thị chi tiết | ✅ | GetProductInfoUseCase |
| 7 | Thêm vào giỏ hàng | ❌ | **CHƯA CÓ** |
| 8 | Thu thập thông tin khách | ❌ | **CHƯA CÓ** |
| 9 | Chốt đơn / chuyển livechat | ❌ | **CHƯA CÓ** |
| 10 | Theo dõi + chăm sóc sau mua | ❌ | **CHƯA CÓ** |

**Tỷ lệ hoàn thành:** **60%** (6/10 steps)

---

## 🎯 Khuyến Nghị

### Priority 1: E-commerce Core Flow
1. **Add to Cart** (Step 7)
   - Intent: `add_to_cart`
   - Use case: `AddToCartUseCase`
   - Cart state trong session

2. **Collect Customer Info** (Step 8)
   - Intent: `collect_customer_info`
   - Use case: `CollectCustomerInfoUseCase`
   - Multi-turn form collection với validation

3. **Place Order** (Step 9)
   - Intent: `place_order`
   - Use case: `PlaceOrderUseCase`
   - Integration với catalog order API

### Priority 2: Support & Post-Purchase
4. **Escalate to Livechat** (Step 9)
   - Intent: `escalate_to_livechat`
   - Use case: `EscalateToLivechatUseCase`
   - Integration với livechat service

5. **Track Order** (Step 10)
   - Intent: `track_order`
   - Use case: `TrackOrderUseCase`
   - Integration với order tracking API

6. **Post-Purchase Care** (Step 10)
   - Intent: `post_purchase_care`
   - Use case: `PostPurchaseCareUseCase`
   - Follow-up automation

### Priority 3: UX Improvements
7. **Guided Filter Questions** (Step 3)
   - Auto-ask filter criteria khi user chỉ nói "xem catalog"
   - Progressive disclosure của filters

8. **Interactive Product Selection** (Step 5)
   - Product list với clickable items
   - Quick replies cho product selection

---

## 📝 Next Steps

1. **Tạo intent definitions** trong `intent_registry.yaml`
2. **Implement use cases** theo Clean Architecture pattern
3. **Add cart management** vào session state
4. **Integration testing** với catalog API
5. **Update test scenarios** trong test-sandbox page

---

**Kết luận:** Flow catalog hiện tại đã cover được **60%** flow mong muốn, tập trung vào phần **browse & search**. Cần implement thêm **e-commerce operations** (cart, checkout, order) để hoàn thiện flow.
