# Kiến trúc "Migration Hub" - Hệ thống Nhập dữ liệu Đa nguồn

Để hỗ trợ nhiều cách migrate khác nhau (Web Scraper, Excel, Shopify, Haravan, v.v.) mà không làm code bị rối, bạn nên áp dụng mô hình **Pluggable Provider Architecture**.

---

## 1. Schema: Thiết kế bảng "Migration Job" Dùng chung
Bảng này đóng vai trò là "Staging Area" (vùng đệm) cho mọi loại nguồn.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Khóa chính. |
| `source_type` | Enum | `web_scraper`, `excel_upload`, `shopify_sync`, `haravan_api`. |
| `status` | Enum | `pending`, `processing`, `staged`, `completed`, `failed`. |
| `batch_metadata` | JSON | Thông tin phụ (URL trang web, Tên tệp Excel, API Key...). |
| `raw_items` | JSONB | Lưu danh sách sản phẩm thô sau khi lấy về (chưa qua xử lý AI). |
| `staged_items` | JSONB | Dữ liệu đã chuẩn hóa (Standardized), sẵn sàng để Confirm. |

---

## 2. Backend: Pattern "Abstract Migration Provider"
Xây dựng một Class cha (Interface) để các Provider con (Scraper, Excel) kế thừa.

```python
class BaseMigrationProvider:
    async def fetch_data(self, params: dict) -> List[dict]:
        """Bước 1: Lấy dữ liệu thô từ nguồn (Scraper cào link, Excel đọc file)"""
        raise NotImplementedError

    async def standardize(self, raw_data: List[dict]) -> List[StandardizedProduct]:
        """Bước 2: Dùng AI hoặc Logic để map về đúng định dạng Catalog của mình"""
        raise NotImplementedError

# Các Provider cụ thể
class WebScraperProvider(BaseMigrationProvider): ...
class ExcelProvider(BaseMigrationProvider): ...
class ShopifyProvider(BaseMigrationProvider): ...
```

**Ưu điểm:** Khi bạn muốn thêm cách migrate từ Haravan, bạn chỉ cần tạo 1 file `haravan_provider.py` mà không cần sửa logic chính của hệ thống.

---

## 3. Quy trình hợp nhất (Unified Workflow)

Mọi cách thức migrate đều phải đi qua 3 bước chuẩn:

1.  **Ingestion (Nạp)**: Đưa dữ liệu vào bảng `MigrationJob`.
2.  **Staging & Preview (Kiểm tra)**: Khách hàng xem trước dữ liệu trên cùng một giao diện (bất kể nguồn từ đâu).
3.  **Commit (Ghi nhận)**: Đẩy dữ liệu từ `MigrationJob` vào các bảng `Product`, `Variant` chính thức.

---

## 4. Frontend: Giao diện "Migration Center"

Thay vì đặt nhiều nút rải rác, hãy tạo một trang/tab **"Migration Center"**:
- **Source Selection**: Các icon chọn nguồn (Web / Excel / Integration).
- **History**: Danh sách các đợt migrate cũ để xem đợt nào thành công, đợt nào lỗi.
- **Unified Preview Table**: Một bảng dữ liệu thông minh, cho phép chỉnh sửa nhanh số lượng lớn sản phẩm trước khi "Import" vào kho kiến thức của Bot.

---

## 5. Lợi ích lâu dài
- **Dễ bảo trì**: Lỗi ở scraper không làm hỏng tính năng import Excel.
- **Tốc độ**: Bạn có thể làm MVP là Scraper trước, sau đó 1 tuần sau thêm Excel rất nhanh.
- **Dữ liệu sạch**: Nhờ có bước "Staging Area", dữ liệu vào Bot luôn được kiểm soát chất lượng qua tay khách hàng.

Bạn có muốn tôi thử thiết kế Schema SQL chi tiết cho bảng `migration_job` này để bạn có thể dùng chung cho mọi loại migrate sau này không?
