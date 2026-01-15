# Catalog Test Steps (Simple)

Mục tiêu: chạy nhanh end-to-end cho catalog (DB → API → bot → frontend).

## 1) Chạy migration DB (catalog backend)
Từ thư mục `catalog/backend`:

```
npm run migrate
```

## 2) Seed dữ liệu mẫu (catalog backend)
Từ thư mục `catalog/backend`:

```
npm run seed:products
```

Kết quả mong đợi:
- Có sản phẩm `published` + `approved`
- Có `stock_status` và `stock_quantity`

## 3) Chạy catalog backend API
Từ thư mục `catalog/backend`:

```
npm run dev
```

Kiểm tra nhanh:
- `GET http://localhost:3001/api/products?type=workflow`
- `GET http://localhost:3001/api/products?type=tool`

Kết quả mong đợi: trả về danh sách sản phẩm (có `price`, `currency`, `stockStatus`, `stockQuantity`).

## 4) Sync vector store (nếu bot dùng search semantic)
Từ thư mục `bot`:

```
python -m backend.scripts.sync_catalog_knowledge
```

## 5) Chạy bot backend
Từ thư mục `bot`:

```
python -m backend.interface.api
```

Kiểm tra nhanh (routing + catalog domain):
- `POST http://localhost:8386/bot/message`
```
{
  "message": "Giá sản phẩm A bao nhiêu?",
  "session_id": "test-001"
}
```
Kết quả mong đợi:
- Không suy diễn giá nếu thiếu data
- Nếu thiếu giá: trả về thông báo thiếu dữ liệu

## 6) Chạy catalog frontend
Từ thư mục `catalog/frontend`:

```
npm run dev
```

Kiểm tra UI:
- `/products`
- `/products/workflow`
- `/products/tools`

Kết quả mong đợi:
- Dữ liệu hiển thị từ API (không dùng mock)
- Search gọi API theo query
- Giá hiển thị đúng hoặc “Chưa có giá”

## 7) Kiểm tra bot embed trên catalog site
Đảm bảo `.env` frontend có:
- `NEXT_PUBLIC_BOT_API_URL` trỏ đúng bot backend
- `NEXT_PUBLIC_BOT_SITE_ID` đúng site id

Mở site và gửi câu hỏi catalog:
- Hỏi giá → chỉ trả lời nếu có data
- Hỏi còn hàng → trả đúng `stockStatus` hoặc báo thiếu dữ liệu
