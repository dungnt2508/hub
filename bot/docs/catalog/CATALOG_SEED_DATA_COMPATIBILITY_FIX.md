# CATALOG SEED DATA COMPATIBILITY FIX

**Ngày fix:** 2024  
**Vấn đề:** Mismatch giữa seed data routing intents và entry handler expected intents

---

## I. VẤN ĐỀ PHÁT HIỆN

### Seed Data Intents (từ `seed_catalog_routing_data.py`)

Pattern rules và routing rules tạo các intent sau:
- `search_products` - Tìm kiếm sản phẩm chung
- `search_by_category` - Tìm sản phẩm theo loại/category
- `query_price` - Hỏi giá sản phẩm
- `query_product_detail` - Xem thông tin chi tiết sản phẩm
- `check_availability` - Kiểm tra còn hàng
- `query_variant` - Hỏi biến thể sản phẩm
- `compare_products` - So sánh sản phẩm

### Entry Handler Expected Intents (trước khi fix)

Entry handler đang expect format:
- `catalog.search` → SearchProductUseCase
- `catalog.info` → GetProductInfoUseCase
- `catalog.compare` → CompareProductsUseCase
- `catalog.availability` → CheckAvailabilityUseCase
- `catalog.price` → GetProductPriceUseCase

### ❌ MISMATCH!

Router trả về intent như `search_products` từ pattern rules, nhưng entry handler expect `catalog.search`.

**Hậu quả:**
- Tất cả requests từ router sẽ bị reject với error "Unknown catalog intent"
- Bot không thể xử lý các câu hỏi về catalog

---

## II. GIẢI PHÁP

### Intent Mapping trong Entry Handler

Thêm `intent_mapping` dictionary trong `CatalogEntryHandler` để map từ router intents (seed data format) sang use case keys.

**File:** `bot/backend/domain/catalog/entry_handler.py`

### Mapping Table

| Router Intent (Seed Data) | Use Case Key | Use Case |
|--------------------------|--------------|----------|
| `search_products` | `catalog.search` | SearchProductUseCase |
| `search_by_category` | `catalog.search` | SearchProductUseCase |
| `query_product_detail` | `catalog.info` | GetProductInfoUseCase |
| `query_variant` | `catalog.info` | GetProductInfoUseCase |
| `query_price` | `catalog.price` | GetProductPriceUseCase |
| `check_availability` | `catalog.availability` | CheckAvailabilityUseCase |
| `compare_products` | `catalog.compare` | CompareProductsUseCase |

### Fallback Strategy

- Nếu intent không có trong mapping → fallback về `catalog.search`
- Log warning để track unknown intents
- Không throw error, vẫn xử lý request

---

## III. CODE CHANGES

### Before

```python
self.use_cases = {
    "catalog.search": SearchProductUseCase(repository),
    "catalog.info": GetProductInfoUseCase(repository),
    # ...
}

# Direct lookup - sẽ fail với seed data intents
if request.intent not in self.use_cases:
    return DomainResponse(status=DomainResult.INVALID_REQUEST, ...)
use_case = self.use_cases[request.intent]
```

### After

```python
self.use_cases = {
    "catalog.search": SearchProductUseCase(repository),
    "catalog.info": GetProductInfoUseCase(repository),
    # ...
}

# Intent mapping: Router intents → Use case keys
self.intent_mapping = {
    "search_products": "catalog.search",
    "search_by_category": "catalog.search",
    "query_product_detail": "catalog.info",
    "query_variant": "catalog.info",
    "query_price": "catalog.price",
    "check_availability": "catalog.availability",
    "compare_products": "catalog.compare",
    # Also support direct use case keys
    "catalog.search": "catalog.search",
    # ...
}

# Map router intent to use case key
use_case_key = self.intent_mapping.get(request.intent)
if not use_case_key:
    # Fallback to search
    use_case_key = "catalog.search"
use_case = self.use_cases[use_case_key]
```

---

## IV. COMPATIBILITY

### ✅ Supported Intent Formats

1. **Seed Data Format** (từ pattern rules):
   - `search_products`, `query_price`, `check_availability`, etc.
   - ✅ Mapped qua `intent_mapping`

2. **Direct Use Case Keys**:
   - `catalog.search`, `catalog.info`, `catalog.price`, etc.
   - ✅ Supported trong `intent_mapping` (identity mapping)

3. **Unknown Intents**:
   - Bất kỳ intent nào không có trong mapping
   - ✅ Fallback về `catalog.search` với warning log

### ✅ Backward Compatibility

- Code cũ vẫn hoạt động (nếu có code nào gọi trực tiếp với `catalog.*` intents)
- Seed data mới hoạt động (router intents từ pattern rules)
- Không breaking changes

---

## V. TESTING RECOMMENDATIONS

### Test Cases

1. **Test với seed data intents:**
   ```python
   request = DomainRequest(
       domain="catalog",
       intent="search_products",  # Seed data format
       ...
   )
   response = await handler.handle(request)
   assert response.status == DomainResult.SUCCESS
   ```

2. **Test với direct use case keys:**
   ```python
   request = DomainRequest(
       domain="catalog",
       intent="catalog.search",  # Direct format
       ...
   )
   response = await handler.handle(request)
   assert response.status == DomainResult.SUCCESS
   ```

3. **Test với unknown intent:**
   ```python
   request = DomainRequest(
       domain="catalog",
       intent="unknown_intent",
       ...
   )
   response = await handler.handle(request)
   # Should fallback to catalog.search
   assert response.status == DomainResult.SUCCESS
   ```

4. **Test end-to-end với router:**
   - Gửi message: "Tìm sản phẩm ChatGPT"
   - Router match pattern → intent: `search_products`
   - Entry handler map → use case: `catalog.search`
   - Use case execute → return products

---

## VI. SUMMARY

### ✅ Fixed

- Intent mapping từ seed data format sang use case keys
- Fallback strategy cho unknown intents
- Backward compatibility với direct use case keys
- Logging để track intent mapping

### ✅ Benefits

- Seed data hoạt động ngay lập tức
- Không cần update seed data
- Flexible mapping cho future intents
- Clear separation giữa router intents và use case keys

### ✅ Status

**COMPATIBLE** - Entry handler giờ đã fit với seed data routing intents.

---

**END OF FIX DOCUMENT**

