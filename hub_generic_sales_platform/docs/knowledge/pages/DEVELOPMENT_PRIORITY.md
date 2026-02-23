# CHIẾN LƯỢC PHÁT TRIỂN & THỨ TỰ ƯU TIÊN (DEVELOPMENT PRIORITY)

Dựa trên mục tiêu **Vietnam Market Fit** và kiến trúc **Generic Sales Platform**, tôi đề xuất lộ trình phát triển Frontend theo 4 giai đoạn.

Mục tiêu cốt lõi: **"Có cái để dùng ngay" (MVP) -> "Bán được hàng" (Operations) -> "Quản lý được" (Reports).**

---

## 🚀 GIAI ĐOẠN 1: KHUNG SƯỜN & KẾT NỐI (Sprint 1 - Foundations)
*Mục tiêu: Bot phải chạy được và chat được "Hello World" trên kênh thật.*

1.  **`Cấu hình / Bot & Kịch bản` (`/bots`)** - **QUAN TRỌNG NHẤT**
    *   **Lý do:** Không có Bot thì không có gì để làm cả. Cần trang này để tạo định danh Bot và gán phiên bản.
2.  **`Cấu hình / Kênh kết nối` (`/integrations`)**
    *   **Lý do:** Bot cần một cái miệng để nói. Cần kết nối ngay với Web Widget hoặc Zalo OA để test thực tế.
3.  **`Công cụ / AI Sandbox` (`/studio`)**
    *   **Lý do:** Dev cần chỗ để test prompt và flow trước khi config cho Bot.

---

## 🧠 GIAI ĐOẠN 2: DỮ LIỆU & TRI THỨC (Sprint 2 - Brains)
*Mục tiêu: Bot phải khôn, hiểu được sản phẩm và trả lời được câu hỏi.*

4.  **`Dữ liệu / Sản phẩm & Dịch vụ` (`/catalog`)** - **CORE VALUE**
    *   **Lý do:** Generic Sales Platform bán cái gì? Phải có trang này để nhập liệu Offering (Căn hộ, Áo thun, Khoá học). Bot không thể tư vấn nếu không biết mình bán gì.
5.  **`Dữ liệu / Tri thức AI` (`/knowledge`)**
    *   **Lý do:** Để Bot trả lời các câu hỏi phụ (Chính sách, Vận chuyển, Pháp lý).

---

## ⚡ GIAI ĐOẠN 3: VẬN HÀNH & CHỐT ĐƠN (Sprint 3 - Operations - Key for VN)
*Mục tiêu: Sale admin nhảy vào chốt đơn khi Bot bí. Đây là tính năng "ăn tiền" ở VN.*

6.  **`Vận hành / Hội thoại` (`/monitor`)** - **MUST HAVE**
    *   **Lý do:** Khách hàng VN rất ghét chat với Bot ngu. Tính năng Monitor + Human Handover là bắt buộc để giữ chân khách. Đây là trang mà nhân viên sẽ mở 24/7.
    *   *Note:* Cần làm trải nghiệm chat mượt mà, real-time banking.

---

## 📊 GIAI ĐOẠN 4: BÁO CÁO & TỐI ƯU (Sprint 4 - Management)
*Mục tiêu: Show số liệu cho Sếp và tối ưu chi phí.*

7.  **`Tổng quan` (`/`)**
    *   **Lý do:** Dashboard đẹp để "lòe" investor/sếp, và xem nhanh tình hình sức khoẻ hệ thống.
8.  **`Báo cáo / Hiệu quả Tư vấn` (`/analytics`)**
    *   **Lý do:** Tối ưu chi phí Token. "Tại sao tháng này đốt nhiều tiền thế?".
9.  **`Báo cáo / Lịch sử Hoạt động` (`/logs`)**
    *   **Lý do:** Debug lỗi khi có sự cố.

---

## 🏁 TÓM TẮT THỨ TỰ THỰC HIỆN

| Thứ tự | Page Path | Nhóm | Lý do |
| :--- | :--- | :--- | :--- |
| **1** | `/bots` | Configuration | Tạo thực thể Bot. |
| **2** | `/studio` | Tools | Test não Bot. |
| **3** | `/catalog` | Data | Nhập liệu sản phẩm để bán. |
| **4** | `/monitor` | Operations | **Killer Feature** cho thị trường VN. |
| **5** | `/` (Dashboard) | Reports | Tổng quan hệ thống. |
| **6** | `/knowledge` | Data | Bổ sung tri thức. |
| **7** | `/analytics` | Reports | Tối ưu vận hành. |

**Lời khuyên:** Hãy tập trung build **`/catalog`** thật tốt (vì nó là trái tim của Generic Platform) và **`/monitor`** thật mượt (vì nó là công cụ kiếm cơm của users).
