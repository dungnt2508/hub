HR DOMAIN
=========

Domain quản lý nhân sự, nghỉ phép, lương.

DOMAIN PURPOSE
--------------

Xử lý các tác vụ nhân sự:
- Tạo đơn xin nghỉ phép
- Tra cứu số ngày phép
- Tra cứu đơn nghỉ phép
- Duyệt/từ chối đơn nghỉ phép

DOMAIN TYPE
-----------

BUSINESS

OPERATION domain với discrete intents.

INTERACTION MODE
----------------

COMMAND

Nhận input → thực thi → trả kết quả.

Không giữ state dài.

Mỗi request độc lập.

ENTRY POINT
-----------

HREntryHandler.handle()

Router gửi DomainRequest với:
- intent: tên intent (ví dụ: "create_leave_request")
- slots: dữ liệu cần thiết (ví dụ: start_date, end_date)

EntryHandler map intent → use case → execute.

ALLOWED RESPONSIBILITIES
------------------------

- Xử lý intent từ router.
- Map intent → use case.
- Thực thi use case.
- Trả DomainResponse với result.
- Validate slots.
- Kiểm tra quyền (RBAC).

FORBIDDEN RESPONSIBILITIES
--------------------------

- Gọi trực tiếp domain khác.
- Quyết định routing domain.
- Giữ state hội thoại dài.
- Phụ thuộc vào frontend.
- Xử lý logic nghiệp vụ ngoài HR.

EXIT CONDITIONS
---------------

Domain trả response khi:
- Use case thực thi xong (SUCCESS).
- Use case lỗi (ERROR).
- Thiếu slots (NEED_MORE_INFO).

Domain không tự chuyển domain.

User muốn chuyển domain → gửi message mới → Router xử lý.

INTENTS
-------

create_leave_request
- Tạo đơn xin nghỉ phép mới.
- Required slots: start_date, end_date, reason.
- Optional slots: leave_type.

query_leave_balance
- Tra cứu số ngày phép còn lại.
- Không cần slots.

query_leave_requests
- Tra cứu danh sách đơn nghỉ phép.
- Không cần slots.

approve_leave
- Duyệt đơn nghỉ phép.
- Required slots: request_id, action.

reject_leave
- Từ chối đơn nghỉ phép.
- Required slots: request_id, reason.
