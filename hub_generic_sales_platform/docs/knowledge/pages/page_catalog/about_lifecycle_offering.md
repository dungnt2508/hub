### Vòng đời của một Offering (Sản phẩm/Dịch vụ/Tài sản):

**1. DRAFT (Nháp):**
- **Khi nào:** Bạn mới khởi tạo một Offering, đang nhập liệu các thuộc tính (Attributes), giá cả, mô tả...
- **Trạng thái:** Chưa sẵn sàng kinh doanh. Bot sẽ không nhìn thấy Offering này.

**2. ACTIVE (Đang kinh doanh):**
- **Khi nào:** Sau khi bạn hoàn tất nhập liệu và nhấn "Publish" phiên bản (Version) đầu tiên.
- **Trạng thái:** Sẵn sàng phục vụ. Bot sẽ sử dụng dữ liệu từ Version đang Active để tư vấn cho khách hàng.

**3. ARCHIVED (Ngừng kinh doanh):**
- **Khi nào:** Offering đã hết vòng đời hoặc không còn được cung cấp (ví dụ: Mẫu xe cũ đã ngừng sản xuất, Dự án bất động sản đã bán hết, Gói vay đã hết hạn).
- **Trạng thái:** Bạn không muốn xóa hẳn (vì cần giữ lịch sử giao dịch, báo cáo, và tri thức cũ), nhưng muốn ẩn hoàn toàn khỏi Bot và các kênh bán hàng hiện tại.

---

### Phân biệt Status của Offering và Version:

| Loại Status | Ý nghĩa | Ví dụ |
| :--- | :--- | :--- |
| **Version Status** | Quản lý **"Nội dung nào đang hiển thị"**. | Version 1 (Draft) -> Version 2 (Active) -> Version 1 (Archived). |
| **Offering Status** | Quản lý **"Offering này có còn tồn tại trong việc kinh doanh hay không"**. | iPhone 15 (Active) -> iPhone 14 (Archived). |

### Ví dụ minh họa:
Bạn đang kinh doanh một **Dự án Căn hộ (Offering)** đang ở trạng thái **Active**. Bạn có 3 phiên bản chính sách bán hàng (Versions).
Đột nhiên, chủ đầu tư thông báo ngừng mở bán vô thời hạn.
-> Thay vì phải vào từng Version để tắt, bạn chỉ cần chuyển **Offering Status** sang **ARCHIVED**. Lập tức toàn bộ Offering này sẽ bị vô hiệu hóa trên mọi kênh, Bot sẽ không còn tư vấn về nó nữa.
