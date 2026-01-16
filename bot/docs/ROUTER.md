ROUTER
======

Router phân loại domain từ user input.

NHIỆM VỤ
---------

Router chỉ làm classification domain.

Router stateless.

Router không xử lý logic nghiệp vụ.

Router không gọi handler domain ngoài entry.

KẾT QUẢ HỢP LỆ
--------------

UNKNOWN là kết quả hợp lệ.

Router không được đoán mò.

Khi không chắc chắn → trả UNKNOWN.

KHI NÀO CHUYỂN DOMAIN
---------------------

Router chuyển domain khi:
- Pattern match thành công.
- Embedding classifier có confidence đủ cao.
- LLM classifier có confidence đủ cao.
- Keyword hint boost domain cụ thể.

Router không chuyển domain khi:
- Tất cả classifier không đủ confidence.
- Không có pattern match.
- → Trả UNKNOWN.

PIPELINE
--------

STEP 0: Session load/create
STEP 0.5: Normalize input
STEP 1: Meta-task detection
STEP 2: Pattern match
STEP 3: Keyword hint
STEP 4: Embedding classifier
STEP 5: LLM classifier (fallback)
STEP 6: UNKNOWN handling

Router chạy tuần tự từ STEP 1 đến STEP 6.
Dừng ngay khi có kết quả đủ confidence.

GIỚI HẠN
---------

Router không:
- Xử lý logic nghiệp vụ.
- Giữ state hội thoại dài.
- Gọi handler domain trực tiếp.
- Quyết định intent trong domain.

Router chỉ:
- Phân loại domain.
- Trả domain name + intent (nếu có).
- Trả UNKNOWN khi không chắc.
