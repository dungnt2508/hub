# DEMO SCENARIO: FINANCE (VAY TÍN CHẤP)
**Tiêu đề:** Duyệt Vay Tiêu Dùng Nhanh (Unsecured Loan)
**Giá trị:** 10 - 100 Triệu VND
**Mô hình:** Generic Sales Platform (Lead Qualification & Scoring)

---

## 1. Sự Khác Biệt Quy Trình

| E-commerce (Cũ) | Generic Sales Platform (Mới) |
| :--- | :--- |
| **Object:** "Gói vay A" | **Object:** "Hạn mức tín dụng" |
| **Action:** "Xem chi tiết" | **Action:** "Check CIC" -> "Prequalify" -> "Duyệt hồ sơ" |
| **Flow:** Static Info | **Flow:** Dynamic Form (Hỏi - Đáp để chấm điểm tín dụng) |

---

## 2. Kịch Bản Hội Thoại (The Script)

**Bối cảnh:** Khách hàng (Chị Lan) cần vay tiền gấp để xoay sở kinh doanh.

**🤖 Iris Fin AI:** Chào chị! Em là trợ lý tài chính F888.
*Chị đang cần hỗ trợ khoản vay khoảng bao nhiêu ạ?*

**👩‍💼 Lan:** Chị cần vay nóng 50 triệu.

**🤖 Iris Fin AI:** Dạ, với khoản vay 50 triệu, bên em có gói **Vay theo Sim** hoặc **Vay theo Đăng ký xe** giải ngân trong 2h.
*Để kiểm tra xem chị có đủ điều kiện duyệt nhanh không, chị cho em hỏi chị đang sinh sống tại khu vực nào ạ?*

**👩‍💼 Lan:** Chị ở Hà Nội.

**🤖 Iris Fin AI:** Dạ, chị có đang có khoản vay nào tại ngân hàng hay tổ chức tín dụng khác không chị Lan nhỉ? (Thông tin này giúp em chọn gói lãi suất tốt nhất cho chị).

**👩‍💼 Lan:** Chị đang trả góp cái điện thoại bên FE thôi.

**🤖 Iris Fin AI:** Dạ tuyệt (Dư nợ thấp).
*Thu nhập hàng tháng của mình (Lương hoặc Kinh doanh) dao động khoảng bao nhiêu ạ?*

**👩‍💼 Lan:** Tầm 15 triệu.

**🤖 Iris Fin AI:** (Running Credit Scoring...)
✅ **Hồ sơ sơ bộ:** Tốt.
Em đề xuất gói **"Kinh Doanh Thần Tốc"**:
- Hạn mức: **50.000.000 VNĐ**
- Kỳ hạn: 12 tháng
- Trả góp: **4.850.000 VNĐ/tháng** (Gốc + Lãi).

*Chị Lan có CMND/CCCD gắn chip ở đó không ạ? Chị chụp gửi em để em lên hồ sơ duyệt online luôn nhé?*

**👩‍💼 Lan:** (Gửi ảnh CCCD)

**🤖 Iris Fin AI:** (OCR Tool extraction...)
Dạ em nhận được rồi: Nguyễn Thị Lan - 0011xx...
Hồ sơ đã được đẩy lên hệ thống thẩm định.
*Khoảng 15 phút nữa sẽ có tin nhắn duyệt hạn mức về điện thoại chị nhé!*

---

## 3. Phân Tích Kỹ Thuật

1.  **Lead Scoring (EKYC & Scoring):**
    *   Bot thu thập `Location`, `Income`, `Debt` để tính `CreditScore`.
    *   Nếu Score thấp -> Từ chối khéo hoặc lái sang gói cầm cố.
    *   Nếu Score cao -> Upsell hạn mức cao hơn.
2.  **Dynamic Form Filling:**
    *   Thay vì bắt khách điền Form dài ngoằng, Bot hỏi từng câu (Conversational Form) để fill vào `Application`.
3.  **Real-time API Integration:**
    *   Bot gọi API `CheckCIC` (giả lập) hoặc `CalculateRepayment` để báo số tiền phải đóng hàng tháng.
