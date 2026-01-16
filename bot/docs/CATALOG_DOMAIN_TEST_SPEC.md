CATALOG DOMAIN - HƯỚNG DẪN TEST
================================

MỤC ĐÍCH
---------
Kiểm tra Catalog Domain hoạt động đúng và tuân thủ Catalog Canon.

CÁCH TEST
---------

CÓ 2 CÁCH:

1. TEST BẰNG SANDBOX (Khuyến nghị)
   - Test trực tiếp qua API
   - Xem kết quả ngay
   - Dễ debug

2. TEST BẰNG FRONTEND
   - Test qua UI
   - Giống user thật
   - Cần frontend chạy

CÁCH 1: TEST BẰNG SANDBOX API
==============================

BƯỚC 1: Chạy Bot Service
------------------------
```bash
cd bot
docker-compose up -d
```

BƯỚC 2: Test qua API
--------------------
```bash
# Test search products
curl -X POST http://localhost:8386/api/admin/test-sandbox \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Tìm sản phẩm laptop",
    "session_id": null
  }'
```

Hoặc dùng Python:
```python
import requests

url = "http://localhost:8386/api/admin/test-sandbox"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}

# Test 1: Search
response = requests.post(url, json={
    "message": "Tìm sản phẩm laptop",
    "session_id": None
}, headers=headers)
print(response.json())
```

CÁCH 2: TEST BẰNG FRONTEND
===========================

BƯỚC 1: Chạy Frontend
--------------------
```bash
cd catalog/frontend
npm run dev
```

BƯỚC 2: Mở browser
------------------
- Truy cập: http://localhost:3001
- Click vào bot widget
- Nhập message test

TEST CASES CỤ THỂ
=================

TEST 1: Search Products
-----------------------
Input: "Tìm sản phẩm laptop"
Expected:
- Domain: catalog
- Intent: search_products
- Response: SUCCESS
- Data có danh sách sản phẩm

Check Canon:
- ✅ Intent không điều hướng state
- ✅ Use case execute trực tiếp

TEST 2: Query Price
------------------
Input: "Giá sản phẩm X bao nhiêu?"
Expected:
- Domain: catalog
- Intent: query_price
- Response: SUCCESS
- Data có giá sản phẩm

Check Canon:
- ✅ Không dùng intent classifier nội bộ
- ✅ Use case execute trực tiếp

TEST 3: Add to Cart
-------------------
Input: "Thêm sản phẩm X vào giỏ hàng"
Expected:
- Domain: catalog
- Intent: add_to_cart
- Response: SUCCESS
- Cart updated in user_context

Check Canon:
- ⚠️ Cart lưu trong user_context, không có state machine
- ⚠️ Canon yêu cầu state machine nhưng code không có

TEST 4: Checkout
---------------
Input: "Thanh toán"
Expected:
- Domain: catalog
- Intent: checkout
- Response: SUCCESS or NEED_MORE_INFO
- Customer info collected

Check Canon:
- ⚠️ Không có state machine cho checkout flow

TEST 5: Track Order
------------------
Input: "Theo dõi đơn hàng ORD-123"
Expected:
- Domain: catalog
- Intent: track_order
- Response: SUCCESS
- Data có order status

Check Canon:
- ✅ Use case execute trực tiếp

CANON VIOLATIONS PHÁT HIỆN
===========================

VIOLATION 1: State Machine Missing
----------------------------------
Canon yêu cầu: "Mọi hành vi catalog do state machine nội bộ xử lý"
Code thực tế: Không có state machine
Impact: Cart, checkout flow không có state management

Test để phát hiện:
```python
# Kiểm tra có state machine không
from bot.backend.domain.catalog import CatalogEntryHandler
handler = CatalogEntryHandler()

# Check: handler có state machine attribute không?
has_state_machine = hasattr(handler, 'state_machine')
print(f"State machine exists: {has_state_machine}")  # Expected: False
```

VIOLATION 2: Signal Emission Missing
------------------------------------
Canon yêu cầu: "Catalog chỉ emit signal khi cần rời domain"
Code thực tế: EscalateToLivechatUseCase không emit signal

Test để phát hiện:
```python
# Test escalate
response = await handler.handle(DomainRequest(
    intent="escalate_support",
    domain="catalog",
    ...
))

# Check: response có signal không?
has_signal = hasattr(response, 'signal') or 'signal' in response.data
print(f"Signal emitted: {has_signal}")  # Expected: False
```

VIOLATION 3: CatalogIntentClassifier Not Used
----------------------------------------------
Canon yêu cầu: "Catalog KHÔNG dùng intent classifier để điều hướng nội bộ"
Code thực tế: CatalogIntentClassifier tồn tại nhưng không dùng trong entry handler

Test để phát hiện:
```python
# Check entry handler có dùng classifier không
import inspect
source = inspect.getsource(CatalogEntryHandler.handle)
uses_classifier = 'CatalogIntentClassifier' in source or 'intent_classifier' in source
print(f"Uses classifier: {uses_classifier}")  # Expected: False ✅
```

CHECKLIST NHANH
===============

✅ PASS
------
- Intent list không expose (domain_registry)
- CatalogIntentClassifier không dùng trong entry handler
- Không có cross-domain calls
- Use cases execute đúng

❌ FAIL
-------
- State machine missing
- Signal emission missing
- State-based flows chưa implement

TEST SCRIPT MẪU
===============

Tạo file: `test_catalog_domain.py`

```python
import asyncio
from bot.backend.domain.catalog.entry_handler import CatalogEntryHandler
from bot.backend.schemas import DomainRequest, DomainResult

async def test_catalog():
    handler = CatalogEntryHandler()
    
    # Test 1: Search
    request = DomainRequest(
        intent="search_products",
        domain="catalog",
        slots={"query": "laptop"},
        user_context={"tenant_id": "test-tenant"}
    )
    
    response = await handler.handle(request)
    
    assert response.status == DomainResult.SUCCESS
    assert "products" in response.data
    print("✅ Test 1 PASS: Search products")
    
    # Test 2: Add to cart
    request = DomainRequest(
        intent="add_to_cart",
        domain="catalog",
        slots={"product_id": "123", "quantity": "1"},
        user_context={"tenant_id": "test-tenant"}
    )
    
    response = await handler.handle(request)
    
    assert response.status == DomainResult.SUCCESS
    assert "cart" in response.data
    print("✅ Test 2 PASS: Add to cart")
    
    # Test 3: Check state machine
    has_state_machine = hasattr(handler, 'state_machine')
    if not has_state_machine:
        print("❌ Test 3 FAIL: State machine missing")
    else:
        print("✅ Test 3 PASS: State machine exists")

if __name__ == "__main__":
    asyncio.run(test_catalog())
```

CHẠY TEST
---------
```bash
cd bot
python -m pytest test_catalog_domain.py -v
```

KẾT LUẬN
=========

Code hiện tại:
- ✅ Use cases hoạt động đúng
- ✅ Intent → use case mapping đúng
- ❌ Thiếu state machine (vi phạm canon)
- ❌ Thiếu signal emission (vi phạm canon)

Cần fix:
1. Implement state machine cho catalog
2. Thêm signal emission mechanism
3. Implement state-based flows
