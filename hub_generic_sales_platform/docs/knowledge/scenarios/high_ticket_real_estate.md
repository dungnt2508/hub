# DEMO SCENARIO: HIGH-TICKET REAL ESTATE SALES
**Tiêu đề:** Bán Căn Hộ Cao Cấp (Sunrise Riverside)
**Giá trị:** ~5 - 7 Tỷ VND
**Mô hình:** Generic Sales Platform (Consultative Selling)

---

## 1. Sự Khác Biệt Quy Trình (The Shift)

| E-commerce (Cũ) | Generic Sales Platform (Mới) |
| :--- | :--- |
| **User:** "Xem giá căn 3PN" | **User:** "Tìm căn 3PN cho gia đình 4 người" |
| **System:** Hiển thị List + Price | **System:** "Anh chị thích tầng cao hay thấp? Hướng nào?" |
| **Action:** "Add to Cart" (Vô lý với nhà) | **Action:** "Tính vay ngân hàng" -> "Đặt lịch xem nhà" |
| **End:** Checkout (Thanh toán online) | **End:** Lead Qualified (Sale gọi chốt cọc) |

---

## 2. Kịch Bản Hội Thoại (The Script)

**Bối cảnh:** Khách hàng (Minh) vào Website Bất động sản, chat với Bot (Iris Real Estate AI).

**👩‍💻 Minh:** Chào shop, mình đang tìm căn hộ 3 phòng ngủ khu vực Quận 7.

**🤖 Iris AI:** Dạ chào anh Minh! Em là trợ lý ảo của Sunrise City.
Hiện bên em đang có đợt quỹ căn 3PN view sông rất đẹp.
*Để tìm căn phù hợp nhất, anh cho em hỏi ngân sách dự kiến của mình khoảng bao nhiêu ạ?*
*(Bot khéo léo Qualify tiền ngay từ đầu)*

**👩‍💻 Minh:** Tầm 6 tỷ quay đầu thôi em.

**🤖 Iris AI:** Dạ, với 6 tỷ thì bên em có 2 lựa chọn cực tốt:
1.  **Căn 3PN (98m2) - Tháp V1:** Tầng trung, View hồ bơi. Giá: **5.8 tỷ**.
2.  **Căn 3PN (105m2) - Tháp V2:** Tầng cao, View sông (Căn góc). Giá: **6.2 tỷ** (Hơi nhỉnh chút nhưng đang có ưu đãi).

*Anh Minh có quan trọng hướng nhà (Đông Tứ Trạch/Tây Tứ Trạch) không ạ?*

**👩‍💻 Minh:** Anh Tây tứ trạch, có căn nào hướng Tây hoặc Tây Bắc không?
À mà căn 6.2 tỷ ưu đãi gì đó?

**🤖 Iris AI:** Dạ **Căn V2-15.04** (View sông) chính là hướng **Tây Bắc**, rất hợp tuổi anh ạ! 🎉
Ưu đãi hiện tại: **Tặng gói nội thất 200tr** và **Miễn phí quản lý 2 năm** nếu chốt trong tháng này.

*Anh có muốn em tính thử bảng tính vay ngân hàng cho căn này không ạ?*

**👩‍💻 Minh:** Ừ tính thử coi. Anh trả trước 30%.

**🤖 Iris AI:** Dạ, em tính sơ bộ cho anh ạ:
- **Giá trị căn hộ:** 6.2 tỷ
- **Vốn tự có (30%):** 1.86 tỷ
- **Vay ngân hàng (70%):** 4.34 tỷ
- **Gốc + Lãi hàng tháng (ước tính 20 năm, ls 8%):** ~45 triệu/tháng.

*Anh Minh thấy mức trả hàng tháng này có thoải mái với dòng tiền của mình không ạ?*

**👩‍💻 Minh:** Cũng hơi căng nhỉ. Nhưng mà nhà đẹp thì cố được.

**🤖 Iris AI:** Dạ, nếu anh ưng căn này thì em khuyên anh nên đi xem thực tế sớm vì căn hướng Tây Bắc view sông này rất hot ạ.
*Em đặt lịch cho Sale bên em dẫn anh đi xem nhà vào **Sáng thứ 7 tuần này (9h)** được không anh?*

**👩‍💻 Minh:** Ok sáng thứ 7 nhé.

**🤖 Iris AI:** Dạ em đã chốt lịch!
👉 **Bùi Văn Tèo** (Senior Sale) sẽ liên hệ anh qua số **090xxx** để đón anh tại sảnh V2.
Em gửi anh Brochure chi tiết qua Zalo nhé. Cảm ơn anh Minh!

---

## 3. Phân Tích Kỹ Thuật (Under the Hood)

Để chạy được kịch bản trên, **Generic Sales Platform** đã kích hoạt các module sau:

1.  **Offering Attribute Search:**
    *   Query: `Category="Apartment" AND Bedrooms=3 AND Price<=6B AND Direction IN ["West", "NorthWest"]`
    *   Khác với E-com chỉ lọc theo Category/Price, ở đây lọc theo `Attribute` động (Hướng nhà).

2.  **Dynamic Pricing & Calculation:**
    *   Tool: `LoanCalculator(price, down_payment_percent, term_years)`
    *   Bot tự gọi Tool để tính ra con số 45 triệu/tháng ngay trong chat.

3.  **Lead Qualification:**
    *   Bot ghi nhận: `Budget=6B`, `FengShui=West Group`, `PaymentCapacity=High`.
    *   Đánh dấu `High Priority Lead`.

4.  **Booking/Scheduling:**
    *   Tool: `BookAppointment(staff_role="Senior_Sale", time="Next Saturday 9AM")`.
    *   Khác với E-com là `CreateOrder`, ở đây Output là một `Appointment`.

## 4. Kết Luận
Đây là ví dụ điển hình cho việc **Dùng Data + Conversation để tạo ra Conversion** trong ngành hàng giá trị cao, điều mà các nền tảng Web bán hàng truyền thống không làm được.
