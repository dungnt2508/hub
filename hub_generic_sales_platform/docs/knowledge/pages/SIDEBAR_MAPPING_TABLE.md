# CẤU TRÚC SIDEBAR: ĐỀ XUẤT CHO THỊ TRƯỜNG VIỆT NAM (2026)

Tài liệu này đề xuất cấu trúc Sidebar mới, tập trung vào **Quy trình Vận hành** (Operation-Centric) thay vì cấu trúc kỹ thuật. Mục tiêu là tối ưu hóa trải nghiệm cho các nhóm người dùng: **Nhân viên tư vấn**, **Quản lý vận hành**, và **Admin kỹ thuật**.

---

## 🏗️ CẤU TRÚC ĐỀ XUẤT (VIETNAM MARKET FIT)

```text
IRIS HUB v4.0.0
├── � Tổng quan (Dashboard)  -> /
├── 💬 Hội thoại (Live Monitor) -> /monitor
├── 📦 Sản phẩm & Dịch vụ (Offerings) -> /catalog
├── 🧠 Tri thức AI (Knowledge) -> /knowledge
├── ⚙️ Cấu hình (Configuration)
│   ├── 🤖 Bot & Kịch bản -> /bots
│   ├── � Kênh kết nối -> /integrations
│   └── 🏢 Tổ chức (Tenants) -> /tenants
├── 📈 Báo cáo (Analytics)
│   ├── 📊 Hiệu quả Tư vấn -> /analytics
│   └── 📜 Lịch sử Hoạt động -> /logs
└── 🛠️ Công cụ (Tools)
    ├── 🧪 AI Sandbox -> /studio
    └── ⚙️ Cài đặt chung -> /settings
```

---

## 🎯 LÝ DO ĐỀ XUẤT

1.  **Tập trung vào "Hội thoại" (`/monitor`)**:
    *   Ở thị trường VN, tính năng "Chat trực tiếp với khách" là quan trọng nhất. Nhân viên sale/CSKH sẽ dành 80% thời gian ở đây để theo dõi Bot và can thiệp (Human Handover) khi cần.
    *   Đưa lên vị trí thứ 2 (ngay sau Dashboard) để truy cập nhanh.

2.  **Dùng thuật ngữ "Sản phẩm & Dịch vụ" (`/catalog`)**:
    *   Thay cho "Product Catalog" để phù hợp với mô hình **Generic Sales Platform** (Bán cả dịch vụ, bất động sản, khóa học...).
    *   Là nơi Quản lý/Admin thường xuyên vào để cập nhật giá, tồn kho.

3.  **Tách riêng "Báo cáo" (`/analytics`, `/logs`)**:
    *   Người Việt thích xem báo cáo chi tiết và minh bạch.
    *   Tách riêng để Quản lý dễ dàng kiểm tra hiệu quả của Bot và nhân viên.

4.  **Gom nhóm "Cấu hình"**:
    *   Bot, Integrations, Tenants là những thứ "Cài đặt một lần" (Set & Forget). Gom lại để đỡ rối mắt cho nhân viên vận hành hàng ngày.

---

## 📋 BẢNG MAPPING CHI TIẾT (MỚI)

| Group | Sidebar Item (VN) | Page Path | Database Tables | Actor Chính | Mục đích |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tổng quan** | **Tổng quan** | `/` | `decision_event` | Owner | Xem doanh thu, chi phí bot, hiệu quả toàn sàn. |
| **Vận hành** | **Hội thoại** | `/monitor` | `runtime_session` | Sale/CSKH | Chat trực tiếp, theo dõi Bot đang tư vấn khách nào. |
| **Dữ liệu** | **Sản phẩm & Dịch vụ** | `/catalog` | `tenant_offering` | Merchandiser | Quản lý kho hàng, giá, thuộc tính Offering. |
| | **Tri thức AI** | `/knowledge` | `bot_faq` | Content Lead | Dạy Bot trả lời câu hỏi, upload tài liệu. |
| **Báo cáo** | **Hiệu quả Tư vấn** | `/analytics` | `decision_event` | Owner | Xem tỷ lệ chốt đơn, chi phí Token/Session. |
| | **Lịch sử Hoạt động** | `/logs` | `runtime_turn` | Admin | Truy vết lỗi, xem lại các đoạn chat cũ. |
| **Cấu hình** | **Bot & Kịch bản** | `/bots` | `bot` | Admin | Tạo Bot, chỉnh sửa luồng (Flow), phiên bản. |
| | **Kênh kết nối** | `/integrations` | `channel_config` | Admin | Kết nối Fanpage, Zalo OA, Website. |
| | **Tổ chức** | `/tenants` | `tenant` | Super Admin | Quản lý các đơn vị kinh doanh (Chi nhánh/Khách hàng). |
| **Công cụ** | **AI Sandbox** | `/studio` | N/A | Dev/Admin | Test prompt và tool trước khi deploy. |
| | **Cài đặt chung** | `/settings` | `user_account` | All | Đổi mật khẩu, cấu hình cá nhân. |

---

## ❓ CÁC CÂU HỎI THƯỜNG GẶP

**1. Tại sao không có mục "Đơn hàng" (Orders)?**
*Answer:* Trong phiên bản hiện tại (v4), IRIS Hub tập trung vào phần **Tư vấn & Chốt đơn (Pre-sales)**. Việc quản lý xử lý đơn hàng (Post-sales) thường được tích hợp với CRM/ERP bên ngoài (KiotViet, SAP, Odoo) hoặc sẽ nằm trong lộ trình v5. Tuy nhiên, thông tin đơn hàng sơ bộ có thể xem tại **Hội thoại** hoặc **Báo cáo**.

**2. "Flow Simulator" (`/channels`) đi đâu rồi?**
*Answer:* Đã được gộp vào luồng **AI Sandbox** hoặc nằm trong quy trình "Test Bot" tại trang `/bots`. Không cần thiết phải nằm ngoài sidebar chính gây rối.

**3. "State Dashboard" (`/routing`) đi đâu rồi?**
*Answer:* Đây là tính năng debugging chuyên sâu. Có thể ẩn khỏi sidebar chính và chỉ truy cập qua **AI Sandbox** hoặc **Hội thoại** (khi click vào chi tiết session).

---
*Cập nhật lần cuối: 08/02/2026 bởi System Architect.*
