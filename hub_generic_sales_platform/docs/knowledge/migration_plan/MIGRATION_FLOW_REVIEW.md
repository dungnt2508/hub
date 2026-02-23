# Review: Luồng Migration → Catalog

## Luồng hiện tại (có vấn đề)

```
Migration: Chọn Bot A → Cào URL → Preview → Confirm
    ↓ (auto redirect)
Catalog: Mở với "Tất cả" → Xem sản phẩm từ mọi domain
```

### Vấn đề

1. **Mất quyền kiểm soát**: User click Confirm xong bị "ném" sang page khác, không có lựa chọn ở lại Migration để cào thêm.

2. **Mâu thuẫn logic domain**:
   - Migration: User **bắt buộc** chọn Bot (domain_id) → sản phẩm gắn với domain đó
   - Catalog sau confirm: Mở "Tất cả" → hiển thị mọi domain gộp chung
   - Người dùng có thể không hiểu: "Tôi chọn Bot A, sao giờ lại xem Tất cả?"

3. **"Tất cả" là workaround**: Chúng ta thêm "Tất cả" chỉ để fix lỗi "không thấy sản phẩm" khi domain không khớp. Nó không phải là thiết kế gốc.

4. **Default Catalog = "Tất cả"**: Khi mở Catalog lần đầu, mặc định là "Tất cả". Với multi-bot, admin thường muốn làm việc trong scope 1 bot/domain, không phải xem hết.

---

## Luồng đề xuất (hợp lý hơn)

### Nguyên tắc
- **Nhất quán domain**: Migration dùng Bot A → Catalog mở với Bot A → thấy đúng sản phẩm vừa lưu
- **User chủ động**: Không tự redirect, để user quyết định đi đâu
- **Rõ ràng**: CTA rõ ràng "Xem trong Catalog" thay vì nhảy trang lặng lẽ

### Thay đổi

| Hiện tại | Đề xuất |
|----------|---------|
| Confirm → auto `router.push("/catalog?view=all")` | Confirm → Stay on Migration, toast + nút "Xem trong Catalog" |
| Catalog `?view=all` → chọn "Tất cả" | Catalog `?bot_id=XXX` → chọn đúng Bot đã dùng khi migrate |
| Catalog mặc định: "Tất cả" | Catalog mặc định: Bot đầu tiên (hoặc bot gần đây) |

### Luồng mới

1. **Migration**: Chọn Bot A → Cào → Preview → Confirm
2. **Sau Confirm**: 
   - Toast: "Đã lưu vào Catalog."
   - Đóng modal
   - (Optional) Hiện banner nhỏ: "Xem X sản phẩm vừa thêm trong Catalog" + nút → chuyển `/catalog?bot_id=BotA`
3. **Catalog**: Khi có `?bot_id=XXX`, pre-select Bot đó → user thấy đúng sản phẩm thuộc domain Bot A
4. **"Tất cả"**: Vẫn giữ cho admin muốn xem cross-domain, nhưng **không** dùng làm default và không dùng sau Migration

---

## Đã triển khai (Option C)

- Confirm → Redirect đến `/catalog?bot_id=XXX` (XXX = Bot đã dùng khi migrate)
- Catalog đọc `?bot_id` và pre-select đúng Bot → user thấy sản phẩm vừa lưu
- Catalog mặc định: Bot đầu tiên (không còn "Tất cả" làm default)
- "Tất cả" vẫn có sẵn khi cần xem cross-domain
