# Danh sách kiểm tra (Checklist) cho Quản trị viên

Dựa trên dữ kiện người dùng cung cấp, dưới đây là các bước cần kiểm tra thủ công:

## 1. Kiểm tra Mirroring (Vũ Thảo báo đã xong)
- [ ] Kết nối vào máy **10.90** (Primary) và chạy script `kiem_tra_mssql_health.sql`.
- [ ] Kết nối vào máy **10.91** (Mirror) và chạy script `kiem_tra_mssql_health.sql`.
- [ ] Xác nhận cột `mirroring_state_desc` hiển thị `SYNCHRONIZED`.
- [ ] Xác nhận vai trò (`mirroring_role_desc`): 10.90 là `PRINCIPAL`, 10.91 là `MIRROR`.

## 2. Kiểm tra Disk (Phúc đã mount disk)
- [ ] Truy cập vào máy **10.90** (Primary) qua Remote Desktop.
- [ ] Mở **Disk Management** hoặc **This PC**.
- [ ] Xác nhận ổ đĩa Backup đã xuất hiện (ví dụ: ổ E:, F:...).
- [ ] Kiểm tra quyền ghi (Write Permission) trên ổ đĩa này cho tài khoản chạy dịch vụ SQL Server.

## 3. Kiểm tra Job Backup
- [ ] Sau khi biết ký tự ổ đĩa (ví dụ ổ `S:`), kiểm tra lại các Job Backup trong SQL Server Agent.
- [ ] Chỉnh sửa Script trong các bước của Job để đảm bảo đường dẫn trỏ đúng vào ổ đĩa vừa mount.
- [ ] Chạy thử (Start Job at Step) một Job Backup để xác nhận file backup được tạo ra trên disk mới.

## 4. Kiểm tra Mirroring trên 10.91
- [ ] Xác nhận con 11.91 (Mirror) đã nhận cấu hình Mirror từ Vũ Thảo. 
- [ ] Lưu ý: Trên con Mirror, các database thường ở trạng thái `RESTORING` (đúng thiết kế của Mirroring).

## 5. (Bổ sung) Sẵn sàng cho Failover trên 10.91
Để đảm bảo khi máy 10.90 chết (Down), máy 10.91 lên làm Chính vẫn có Backup:
- [ ] **Disk**: Yêu cầu Phúc mount cùng loại Disk (hoặc trỏ về cùng 1 Server lưu trữ backup) lên máy 10.91. Phải đảm bảo cùng ký tự ổ đĩa (Drive Letter) để Job chạy không lỗi.
- [ ] **Job**: Thực hiện Script out (Generate Script) các Job từ máy 10.90 và chạy trên máy 10.91.
- [ ] **Lưu ý**: Các Job trên 10.91 nên được để ở trạng thái **Disabled** (Tắt) hoặc viết script kiểm tra `PRINCIPAL` bên trong để tránh báo lỗi khi máy đang ở mode Mirror.
