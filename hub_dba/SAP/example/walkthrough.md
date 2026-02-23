# Walkthrough: SAP Monitoring & Incident Response Guide

Dưới đây là tóm tắt các công cụ và kịch bản bạn có thể sử dụng ngay để xử lý sự cố trong mùa cao điểm.

## 1. Các T-code Giám sát Cơ bản (Real-time)
| T-code | Mục đích | Lưu ý quan trọng |
| :--- | :--- | :--- |
| **AL08** | Toàn bộ User online | Xem cột `Application` và `Memory`. |
| **SM50** | Quản lý Work Process | Tìm các process ở trạng thái `Priv` hoặc `Running` quá lâu. |
| **SM12** | Quản lý bản ghi bị khóa | Kiểm tra nếu có lock tồn tại > 30 phút. |
| **SM13** | Quản lý lỗi Update | Đảm bảo không có dòng nào bị `Error`. |
| **ST06** | Sức khỏe OS | CPU utilization không nên vượt quá 85%. |

## 2. Kịch bản Xử lý nhanh (Quick Fixes)
### Kịch bản A: User chạy báo cáo quá nặng gây treo server
1. Dùng **SM04** tìm User đó.
2. Menu `User` -> `Log off` -> `Local` hoặc `System-wide`.
3. Nếu vẫn không thoát, vào **SM50**, chọn process của user đó và chọn `Process` -> `Cancel` -> `Without Core`.

### Kịch bản B: Post thông báo bảo trì khẩn cấp
1. Dùng **SM02**.
2. Nhấn `Create`, nhập nội dung và chọn thời gian hết hạn.
3. Nhấn `Save` để tất cả user nhận được thông báo.

### Kịch bản C: Instance bị treo hoàn toàn (Không vào được SAP Logon)
- Dùng công cụ **SAP MMC** trên Windows hoặc lệnh `sapcontrol` ở OS:
  - `sapcontrol -nr [ID] -function RestartInstance`

## 3. Checklist Dọn dẹp (Housekeeping) hàng ngày
- [ ] Xóa Spool cũ (Report `RSPO0041`).
- [ ] Xóa Job Log cũ (Report `RSBTCDEL2`).
- [ ] Kiểm tra lỗi Short Dumps (`ST22`).

> [!IMPORTANT]
> Trong mùa cao điểm, hãy ưu tiên tài nguyên cho các giao dịch quan trọng (Sales, Delivery). Tạm dừng hoặc dời các Backgroud Job nặng sang ban đêm.
