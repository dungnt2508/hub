INTERACTION FLOW
================

Luồng xử lý từ user input đến domain exit.

TỔNG QUAN
----------

User Input → Router → Domain → Exit

Router chạy MỘT LẦN tại entry point.
Sau khi vào domain, domain toàn quyền xử lý.

CHI TIẾT
--------

1. User gửi message
   - Input: raw_message, user_id, session_id
   - Entry: API Handler

2. Router nhận request
   - RouterOrchestrator.route()
   - Load/create session
   - Normalize input

3. Router classification
   - Pattern match
   - Keyword hint
   - Embedding classifier
   - LLM classifier (fallback)
   - → Domain name + intent (nếu có)
   - → UNKNOWN (nếu không chắc)

4. Domain nhận request
   - DomainDispatcher khởi tạo handler
   - EntryHandler.handle()
   - Domain xử lý toàn quyền

5. Domain xử lý
   - OPERATION: map intent → use case → execute
   - STATEFUL: state machine xử lý
   - KNOWLEDGE: query knowledge base
   - META: xử lý meta task

6. Domain trả response
   - DomainResponse với result
   - Status: SUCCESS / ERROR / NEED_MORE_INFO

7. Exit
   - Domain hoàn thành.
   - Session lưu state (nếu cần).
   - Response trả về user.

CHUYỂN DOMAIN
-------------

Chuyển domain chỉ được thực hiện bởi Router.

Domain không tự chuyển domain.

User muốn chuyển domain → gửi message mới → Router chạy lại.

STATEFUL DOMAIN
---------------

Catalog domain (STATEFUL):
- Giữ state trong session.
- State machine xử lý browse, filter, refine.
- Chỉ emit signal khi cần rời domain.

COMMAND DOMAIN
--------------

HR, DBA domain (COMMAND):
- Nhận input → thực thi → trả kết quả.
- Không giữ state dài.
- Mỗi request độc lập.

QA DOMAIN
---------

Knowledge domain (QA):
- Hỏi–đáp tri thức.
- Không giữ state dài.
- Mỗi query độc lập.

LƯU Ý
-----

Router chỉ chạy tại entry point.

Domain xử lý toàn bộ hội thoại trong domain đó.

Domain không biết domain khác tồn tại.

Frontend không quyết định domain.
