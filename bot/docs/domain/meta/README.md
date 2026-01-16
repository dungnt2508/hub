META DOMAIN
===========

Domain xử lý các tác vụ meta như chào hỏi, cảm ơn.

DOMAIN PURPOSE
--------------

Xử lý các tác vụ meta:
- Chào hỏi
- Cảm ơn
- Small talk
- Hệ thống tasks

DOMAIN TYPE
-----------

META

INTERACTION MODE
----------------

CONVERSATIONAL

Xử lý hội thoại ngắn, không giữ state dài.

Mỗi task độc lập.

ENTRY POINT
-----------

MetaEntryHandler.handle()

Router gửi DomainRequest với task.

EntryHandler xử lý task động, không có intent tĩnh.

ALLOWED RESPONSIBILITIES
------------------------

- Xử lý meta task từ router.
- Xử lý chào hỏi, cảm ơn.
- Xử lý small talk.
- Trả DomainResponse với response.
- Không cần intent tĩnh.

FORBIDDEN RESPONSIBILITIES
--------------------------

- Expose intent list tĩnh.
- Gọi trực tiếp domain khác.
- Quyết định routing domain.
- Giữ state hội thoại dài.
- Phụ thuộc vào frontend.
- Xử lý logic nghiệp vụ ngoài Meta.

EXIT CONDITIONS
---------------

Domain trả response khi:
- Task xử lý xong (SUCCESS).
- Task lỗi (ERROR).

Domain không tự chuyển domain.

User muốn chuyển domain → gửi message mới → Router xử lý.

TASK PROCESSING
---------------

Meta domain xử lý task động:
- Nhận task từ router.
- Xử lý chào hỏi, cảm ơn, small talk.
- Trả response.

Không có intent list tĩnh.

Mỗi task được xử lý độc lập.
