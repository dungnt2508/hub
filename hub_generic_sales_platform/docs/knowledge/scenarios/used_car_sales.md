# DEMO SCENARIO: USED CAR SALES (OTO LƯỚT)
**Tiêu đề:** Mua Bán Xe Ô tô Cũ (Used Car Trading)
**Giá trị:** 300 Triệu - 2 Tỷ VND
**Mô hình:** Generic Sales Platform (Asset Trading)

---

## 1. Sự Khác Biệt Quy Trình

| E-commerce (Cũ) | Generic Sales Platform (Mới) |
| :--- | :--- |
| **Object:** "Xe Mazda 3" | **Object:** "Asset (Tài sản) có tình trạng cụ thể" |
| **Attributes:** Màu, Giá | **Attributes:** ODO, Năm SX, Biển số, Lịch sử đâm đụng, Độ xe |
| **Flow:** Mua ngay | **Flow:** "Định giá xe cũ" -> "Đổi xe (Trade-in)" -> "Lái thử" |

---

## 2. Kịch Bản Hội Thoại (The Script)

**Bối cảnh:** Khách hàng (Tùng) muốn đổi xe Morning cũ lên Mazda 3.

**🤖 Iris Auto AI:** Chào anh Tùng! Chào mừng anh đến với AnyCar.
*Anh đang tìm dòng xe Sedan, SUV hay muốn bán xe cũ ạ?*

**👨‍🔧 Tùng:** Anh muốn tìm con Mazda 3 lướt, đời cao chút.

**🤖 Iris Auto AI:** Dạ, Mazda 3 bên em mới về 3 chiếc cực đẹp:
1.  **Mazda 3 Luxury (2022) - Trắng:** ODO 1.5 vạn, Biển HN. Giá: **580tr**.
2.  **Mazda 3 Premium (2023) - Đỏ:** ODO 8000km, Biển Tỉnh. Giá: **635tr**.

*Anh Tùng ưu tiên màu sắc hay quan trọng về ODO/Đời xe hơn ạ?*

**👨‍🔧 Tùng:** Màu trắng đi. Mà chiếc 2022 đó có bớt không? Anh có con Morning 2018 muốn đổi bù trừ.

**🤖 Iris Auto AI:** Dạ, bên em có chương trình **"Thu cũ đổi mới - Trợ giá 10 triệu"** ạ! 🚗
Để em định giá sơ bộ con Morning của anh nhé:
*Xe anh Morning bản nào (MT/AT, Si/S), đi được bao nhiêu km rồi ạ?*

**👨‍🔧 Tùng:** Bản Si AT, đi 6 vạn rồi. Xe gia đình, không dịch vụ.

**🤖 Iris Auto AI:** (Tra bảng giá thu mua)
Dạ với Morning Si AT 2018, ODO 6 vạn, chất xe đẹp:
Bên em có thể thu mua khoảng **230 - 245 triệu**.

Như vậy nếu lấy con **Mazda 3 Luxury (580tr)**, anh chỉ cần bù khoảng **335 triệu** thôi ạ.
*Anh có muốn em mang con Mazda 3 qua nhà cho anh lái thử và nhân tiện thợ bên em xem xe Morning của anh luôn không?*

**👨‍🔧 Tùng:** Được đấy. Sáng mai nhé.

---

## 3. Phân Tích Kỹ Thuật

1.  **Trade-in Logic (Thu cũ đổi mới):**
    *   Hệ thống không chỉ "Bán" (Sell) mà còn "Mua" (Buy/Trade-in).
    *   Bot có tool `EstimateCarValue(model, year, odo)` để định giá xe cũ của khách.
2.  **Inventory Metadata:**
    *   Offering có các attribute sâu: `ODO`, `PlateCity` (Biển Tỉnh/Phố), `OwnerHistory` (1 chủ từ đầu).
3.  **Mobile Service:**
    *   Booking `TestDriveHome` (Lái thử tại nhà) - Dịch vụ cao cấp của ngành xe.
