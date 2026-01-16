KNOWLEDGE DOMAIN
================

Domain hỏi đáp dựa trên knowledge base.

DOMAIN PURPOSE
--------------

Xử lý các câu hỏi tri thức:
- Hỏi đáp về chính sách
- Hỏi đáp về quy trình
- Hỏi đáp về kiến thức chung

DOMAIN TYPE
-----------

KNOWLEDGE

INTERACTION MODE
----------------

QUERY

Hỏi–đáp tri thức, không giữ state dài.

Mỗi query độc lập.

ENTRY POINT
-----------

KnowledgeEntryHandler.handle()

Router gửi DomainRequest với query.

EntryHandler xử lý query động, không có intent tĩnh.

ALLOWED RESPONSIBILITIES
------------------------

- Xử lý query từ router.
- Query knowledge base (RAG).
- Trả DomainResponse với answer.
- Không cần intent tĩnh.

FORBIDDEN RESPONSIBILITIES
--------------------------

- Expose intent list tĩnh.
- Gọi trực tiếp domain khác.
- Quyết định routing domain.
- Giữ state hội thoại dài.
- Phụ thuộc vào frontend.
- Xử lý logic nghiệp vụ ngoài Knowledge.

EXIT CONDITIONS
---------------

Domain trả response khi:
- Query xử lý xong (SUCCESS).
- Query lỗi (ERROR).
- Không tìm thấy answer (NOT_FOUND).

Domain không tự chuyển domain.

User muốn chuyển domain → gửi message mới → Router xử lý.

QUERY PROCESSING
----------------

Knowledge domain xử lý query động:
- Nhận query từ router.
- Query knowledge base qua RAG.
- Trả answer.

Không có intent list tĩnh.

Mỗi query được xử lý độc lập.
