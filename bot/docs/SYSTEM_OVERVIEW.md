SYSTEM OVERVIEW
===============

Hệ thống chatbot đa domain dùng domain routing tầng cao.

KIẾN TRÚC TỔNG QUAN
-------------------

Hệ thống gồm 4 thành phần chính:

1. Router
   - Phân loại domain từ user input.
   - Chạy MỘT LẦN tại entry point.
   - Stateless, không xử lý nghiệp vụ.

2. Domain
   - Đơn vị nghiệp vụ độc lập.
   - Toàn quyền xử lý ngữ cảnh nội bộ.
   - Không gọi trực tiếp domain khác.

3. Registry
   - Chứa metadata domain.
   - Không khởi tạo handler.
   - Single source of truth.

4. Interaction Mode
   - STATEFUL: giữ context, có state machine.
   - COMMAND: nhận input → thực thi → trả kết quả.
   - QA: hỏi–đáp tri thức, không giữ state dài.

DOMAIN TYPES
------------

- BUSINESS: xử lý nghiệp vụ chính (HR, DBA, Catalog).
- META: chào hỏi, cảm ơn, small talk.
- SYSTEM: routing, fallback, health check.

LUỒNG XỬ LÝ
-----------

User input → Router → Domain → Exit

Router quyết định domain.
Domain xử lý toàn bộ hội thoại trong domain đó.
Chuyển domain chỉ được thực hiện bởi Router.

NGUYÊN TẮC
----------

- Domain là ngữ cảnh nghiệp vụ ổn định.
- Router chỉ làm classification.
- Registry chỉ chứa metadata.
- Domain không phụ thuộc frontend.
