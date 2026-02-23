# Kịch bản Demo: "Sales Agent" (Chuyên gia Bán hàng)

## Mục tiêu
Chứng minh bot không chỉ trả lời câu hỏi mà còn biết:
1.  **Tra cứu Tồn kho** (Inventory Check).
2.  **Báo giá Chính xác** (Pricing Engine).
3.  **Chốt đơn & Upsell** (Closing).

## Chuẩn bị
1.  Mở terminal, chạy lệnh seed data:
    ```bash
    python -m scripts.seed_data
    ```
    *(Đảm bảo đã cài đặt environment và active virtualenv)*

2.  Khởi động Bot:
    ```bash
    uvicorn app.main:app --reload
    ```

## Kịch bản (Chat Flow)

### Bước 1: Khách hàng hỏi mông lung (Tìm kiếm)
*User đóng vai khách hàng đang tìm mua xe Vios.*

**User**: "Bên mình có xe Vios không?"
**Bot**: "Dạ có ạ, bên em đang có **Toyota Vios 1.5G 2024 (Bạc)**. Vua doanh số, bền bỉ, tiết kiệm nhiên liệu..."
*(Bot tìm thấy sản phẩm vừa seed)*

### Bước 2: Khách hàng kiểm tra kho (Inventory Check)
**User**: "Xe này còn hàng ở Hà Nội không?"
**Bot**: "Dạ, hiện tại kho **Tổng (Hà Nội)** vẫn còn **[X]** chiếc sẵn sàng giao ngay ạ."
*(Bot tra cứu bảng TenantInventoryItem, số lượng > 0)*

### Bước 3: Khách hàng hỏi giá (Pricing Check)
**User**: "Giá lăn bánh bao nhiêu?"
**Bot**: "Dạ, giá niêm yết của Vios 1.5G 2024 là **530.000.000 VND**. Anh/chị có muốn em tính chi phí lăn bánh tạm tính luôn không ạ?"
*(Bot tra cứu bảng TenantVariantPrice)*

### Bước 4: Chốt đơn & Upsell (Decision & Closing)
**User**: "Ok, tôi muốn đặt cọc chiếc này."
**Bot**: "Tuyệt vời ạ! Để làm thủ tục đặt cọc, em cần xin thêm thông tin CMND/CCCD để soạn hợp đồng. Ngoài ra, bên em đang có gói phụ kiện giảm 50% cho Vios, anh/chị có quan tâm không ạ?"
*(Bot chuyển sang trạng thái PURCHASING và gợi ý Upsell)*

## Lưu ý
- Nếu Bot hỏi lại "Bạn muốn tìm xe màu gì?", hãy trả lời "Màu bạc" hoặc "Bản G".
- Số lượng tồn kho là ngẫu nhiên (1-3 chiếc) mỗi lần chạy seed.
