# DEMO SCENARIO: EDUCATION ADMISSIONS (TUYỂN SINH)
**Tiêu đề:** Tuyển Sinh Khoá Luyện Thi IELTS 
**Giá trị:** ~15 - 50 Triệu VND/Khóa
**Mô hình:** Generic Sales Platform (Consultative Selling)

---

## 1. Sự Khác Biệt Quy Trình

| E-commerce (Cũ) | Generic Sales Platform (Mới) |
| :--- | :--- |
| **Object:** "Khoá học IELTS" | **Object:** "Lộ trình học cá nhân hóa" |
| **Action:** "Mua ngay" | **Action:** "Test trình độ" -> "Tư vấn lộ trình" -> "Đăng ký học thử" |
| **Price:** Cố định (5.000.000đ) | **Price:** Dynamic (Dựa trên Entry Level & Target) |

---

## 2. Kịch Bản Hội Thoại (The Script)

**Bối cảnh:** Học sinh (Nam) vào Website trung tâm Anh ngữ IvyPrep.

**🤖 Iris Edu AI:** ChChào bạn! Mình là trợ lý tuyển sinh của IvyPrep. 
*Bạn đang quan tâm đến khoá học nào (IELTS, TOEIC, Giao tiếp) hay cần mình tư vấn lộ trình?*

**👨‍🎓 Nam:** Mình muốn học IELTS cấp tốc.

**🤖 Iris Edu AI:** Dạ, để tư vấn lớp phù hợp, cho mình hỏi:
*Target mong muốn của bạn là bao nhiêu (VD: 6.5, 7.0)? Và khi nào bạn cần thi?*

**👨‍🎓 Nam:** Mình cần 6.5 để tháng 9 nộp hồ sơ du học. Giờ mình chưa biết test ở đâu.

**🤖 Iris Edu AI:** Dạ vâng, còn khoảng 6 tháng.
*Bạn đã từng thi IELTS chưa hay đây là lần đầu? Tự đánh giá trình độ hiện tại khoảng bao nhiêu ạ?*

**👨‍🎓 Nam:** Chưa thi bao giờ, chắc tầm 4.0 thôi.

**🤖 Iris Edu AI:** Dạ, vậy lộ trình tối ưu sẽ là: **Foundation (4.0-5.0)** -> **Intermediate (5.0-6.0)** -> **Intensive (6.0-6.5+)**.
Tổng thời gian khoảng 5-6 tháng.

Hiện bên mình đang có **Học bổng Early Bird (Giảm 20%)** cho khoá Foundation khai giảng ngày 15/06.
*Bạn có muốn làm bài Test Online ngắn (15p) để xếp lớp chính xác không ạ?*

**👨‍🎓 Nam:** Ok gửi mình link test.

**🤖 Iris Edu AI:** (Gửi Link Test & Chờ kết quả)
...
*Chúc mừng Nam! Kết quả Reading/Listening của bạn khá tốt (4.5).*
Bạn đủ điều kiện vào thẳng lớp **Pre-IELTS (Target 5.5)** luôn nhé! Tiết kiệm được 2 tháng so với dự kiến.

Học phí cho lộ trình cam kết 6.5 này là: **32.000.000 VNĐ** (Đã trừ ưu đãi).
*Bạn muốn mình đặt lịch tư vấn trực tiếp với Giáo viên tại cơ sở Quận 3 vào chiều nay không?*

**👨‍🎓 Nam:** Chiều nay bận rồi, tối mai nhé.

**🤖 Iris Edu AI:** Dạ đã note lịch tối mai 19h tại IvyPrep Võ Văn Tần cho bạn Nam.

---

## 3. Phân Tích Kỹ Thuật

1.  **Placement Testing:**
    *   Bot tích hợp tool `AssignTest` và nhận kết quả realtime để `RecommendLevel`.
2.  **Personalized Pathway:**
    *   Offering không phải là 1 khóa học lẻ, mà là một `Bundle` (Combo) dựa trên `Current Level` và `Target`.
3.  **Scheduling:**
    *   Booking cuộc hẹn tư vấn chuyên sâu (Consultation) thay vì bán hàng trực tiếp.
