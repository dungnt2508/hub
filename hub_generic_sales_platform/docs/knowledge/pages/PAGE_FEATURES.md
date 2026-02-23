# TÀI LIỆU MÔ TẢ TÍNH NĂNG CÁC TRANG (PAGE FEATURES GUIDE)

Tài liệu này mô tả chi tiết chức năng và đối tượng sử dụng của các trang trong hệ thống IRIS Hub v4, tương ứng với cấu trúc Sidebar mới dành cho thị trường Việt Nam.

---

## 1. NHÓM VẬN HÀNH (OPERATIONS)

Nhóm chức năng dành cho các nhân viên Sale và Chăm sóc khách hàng (CSKH), những người trực tiếp tương tác với người dùng cuối.

### 💬 HỘI THOẠI (`/monitor`)
*Trung tâm chỉ huy của nhân viên tư vấn.*

*   **Tính năng chính:**
    *   **Live Chat Monitor:** Xem danh sách các đoạn chat đang diễn ra theo thời gian thực.
    *   **Human Handover:** Nút "Tiếp quản" để nhân viên nhảy vào chat thay Bot khi Bot gặp khó khăn hoặc khách yêu cầu gặp người.
    *   **Session Detail:** Xem chi tiết ngữ cảnh của khách hàng (Khách đang quan tâm sản phẩm nào, ngân sách bao nhiêu, trạng thái tâm lý).
    *   **Filter:** Lọc hội thoại theo trạng thái (Đang chat, Cần hỗ trợ, Đã chốt đơn).

---

## 2. NHÓM DỮ LIỆU (DATA)

Nhóm chức năng dành cho Quản lý sản phẩm (Merchandiser) và Quản lý nội dung (Content Lead).

### 📦 SẢN PHẨM & DỊCH VỤ (`/catalog`)
*Nơi quản lý "Kho hàng" của doanh nghiệp.*

*   **Tính năng chính:**
    *   **Quản lý Offering:** Thêm/Sửa/Xóa các Sản phẩm, Dịch vụ, Dự án bất động sản.
    *   **Dynamic Attributes:** Cấu hình các thuộc tính động tùy theo ngành hàng (VD: BĐS có "Hướng nhà", Thời trang có "Size/Màu").
    *   **Giá & Tồn kho:** Cập nhật bảng giá (Price List) và trạng thái tồn kho (Inventory).
    *   **Version Control:** Quản lý các phiên bản dữ liệu (Draft, Active, Archived) để đảm bảo Bot luôn dùng dữ liệu chuẩn.

### 🧠 TRI THỨC AI (`/knowledge`)
*Bộ não và sách giáo khoa cho Bot.*

*   **Tính năng chính:**
    *   **FAQ Management:** Quản lý bộ câu hỏi thường gặp.
    *   **Sales Scenarios:** Định nghĩa các kịch bản tư vấn bán hàng (Use Cases).
    *   **Semantic Cache:** Xem và tinh chỉnh các câu trả lời được cache để tối ưu tốc độ và chi phí.
    *   **Tài liệu:** Upload tài liệu (PDF, Docx) để Bot tự học (RAG).

---

## 3. NHÓM BÁO CÁO (REPORTS)

Nhóm chức năng dành cho Chủ doanh nghiệp (Owner) và Quản lý vận hành.

### 📊 TỔNG QUAN (`/`)
*Bức tranh toàn cảnh về sức khỏe doanh nghiệp.*

*   **Tính năng chính:**
    *   **Real-time Stats:** Số lượng khách đang online, số đơn hàng vừa chốt.
    *   **Business Metrics:** Doanh thu ước tính, Tỷ lệ chuyển đổi (Conversion Rate).
    *   **System Health:** Trạng thái hoạt động của các Bot và dịch vụ vệ tinh.

### 📈 HIỆU QUẢ TƯ VẤN (`/analytics`)
*Phân tích sâu về hiệu suất của Bot.*

*   **Tính năng chính:**
    *   **Funnel Analysis:** Phễu chuyển đổi khách hàng (Từ Xem -> Quan tâm -> Chốt).
    *   **Cost Analysis:** Chi phí Token, chi phí trên mỗi đoạn hội thoại.
    *   **Topic Analysis:** Các chủ đề khách hàng hay hỏi nhất.

### 📜 LỊCH SỬ HOẠT ĐỘNG (`/logs`)
*Hộp đen ghi lại mọi sự kiện.*

*   **Tính năng chính:**
    *   **Audit logs:** Ai đã sửa giá? Ai đã đổi cấu hình Bot?
    *   **System logs:** Các lỗi kỹ thuật, cảnh báo hệ thống.
    *   **Traceability:** Truy vết lịch sử ra quyết định của Bot (Tại sao Bot lại trả lời như thế này?).

---

## 4. NHÓM CẤU HÌNH (CONFIGURATION)

Nhóm chức năng dành cho Admin hệ thống và IT.

### 🤖 BOT & KỊCH BẢN (`/bots`)
*Xưởng chế tạo Robot.*

*   **Tính năng chính:**
    *   **Bot Registry:** Tạo mới và quản lý danh sách Bot.
    *   **Flow Design:** Cấu hình luồng đi của Bot (Flow Config).
    *   **Personality:** Cài đặt tính cách, giọng văn cho Bot.

### 🔌 KÊNH KẾT NỐI (`/integrations`)
*Cổng giao tiếp với thế giới bên ngoài.*

*   **Tính năng chính:**
    *   **Channel Connect:** Kết nối Fanpage Facebook, Zalo OA, Website Widget, Telegram.
    *   **API Keys:** Quản lý Key kết nối với các hệ thống ERP/CRM.

### 🏢 TỔ CHỨC (`/tenants`)
*Quản lý đa chi nhánh/đa khách hàng.*

*   **Tính năng chính:**
    *   **Tenant Management:** Tạo và cấu hình các đơn vị kinh doanh.
    *   **User Management:** Quản lý tài khoản nhân viên và phân quyền (Roles).

---

## 5. NHÓM CÔNG CỤ (TOOLS)

Nhóm chức năng dành cho Đội ngũ phát triển (Dev) và Vận hành viên cao cấp.

### 🧪 AI SANDBOX (`/studio`)
*Phòng thí nghiệm AI.*

*   **Tính năng chính:**
    *   **Prompt Lab:** Thử nghiệm và tinh chỉnh các câu lệnh Prompt.
    *   **Tool Testing:** Test các công cụ (Tool) của Bot trước khi đưa vào hoạt động.
    *   **Simulation:** Giả lập các đoạn hội thoại mẫu để kiểm tra phản ứng của Bot.

### ⚙️ CÀI ĐẶT CHUNG (`/settings`)
*Cài đặt cá nhân và tài khoản.*

*   **Tính năng chính:**
    *   **Profile:** Đổi mật khẩu, cập nhật thông tin cá nhân.
    *   **Preferences:** Cài đặt ngôn ngữ, giao diện (Dark/Light mode).

---
*Tài liệu này được cập nhật theo phiên bản IRIS Hub v4.0.0 (2026).*
