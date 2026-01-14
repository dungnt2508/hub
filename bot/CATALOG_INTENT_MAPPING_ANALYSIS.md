# CATALOG INTENT MAPPING ANALYSIS

## VẤN ĐỀ PHÁT HIỆN

### Seed Data Intents (từ `seed_catalog_routing_data.py`)

Pattern rules tạo các intent:
- `search_products` - Tìm kiếm sản phẩm chung
- `search_by_category` - Tìm sản phẩm theo loại/category
- `query_price` - Hỏi giá sản phẩm
- `query_product_detail` - Xem thông tin chi tiết sản phẩm
- `check_availability` - Kiểm tra còn hàng
- `query_variant` - Hỏi biến thể sản phẩm
- `compare_products` - So sánh sản phẩm

### Entry Handler Expected Intents (hiện tại)

Entry handler đang expect:
- `catalog.search` → SearchProductUseCase
- `catalog.info` → GetProductInfoUseCase
- `catalog.compare` → CompareProductsUseCase
- `catalog.availability` → CheckAvailabilityUseCase
- `catalog.price` → GetProductPriceUseCase

### ❌ MISMATCH!

Router sẽ trả về intent như `search_products`, nhưng entry handler expect `catalog.search`.

## GIẢI PHÁP

Cần tạo intent mapper trong `CatalogEntryHandler` để map từ router intents (seed data format) sang use case keys.

