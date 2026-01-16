SYSTEM PURPOSE
--------------
Hệ thống chatbot đa domain, dùng domain routing tầng cao.
Mỗi domain là một đơn vị nghiệp vụ độc lập, sở hữu toàn quyền xử lý ngữ cảnh nội bộ.
Mục tiêu: đúng kiến trúc, mở rộng được, không loạn tư duy.

DOMAIN LAW
----------
- Domain là ngữ cảnh nghiệp vụ ổn định, không phải intent nhỏ.
- Router chỉ chạy MỘT LẦN tại entry point.
- Sau khi vào domain, domain toàn quyền xử lý hội thoại.
- Domain KHÔNG được gọi trực tiếp domain khác.
- Chuyển domain chỉ được thực hiện bởi Router.
- Domain không được phụ thuộc vào frontend.

ROUTER LAW
----------
- Router chỉ làm classification domain.
- Router stateless.
- Router không xử lý logic nghiệp vụ.
- Router không gọi handler domain ngoài entry.
- UNKNOWN là kết quả hợp lệ, không được đoán mò.

CATALOG CANON
-------------
- Catalog là STATEFUL domain.
- Catalog phục vụ exploration, không phải command execution.
- Catalog KHÔNG expose intent list.
- Catalog KHÔNG intent tĩnh.
- Catalog KHÔNG dùng intent classifier để điều hướng nội bộ.
- Mọi hành vi catalog (browse, filter, refine, compare) do state machine nội bộ xử lý.
- Catalog chỉ emit signal khi cần rời domain (ví dụ: mua hàng).

INTENT LAW
----------
- Intent chỉ tồn tại trong OPERATION domain.
- Intent là command rõ ràng, một-shot.
- Intent không dùng cho hội thoại dài.
- Một intent chỉ thuộc MỘT domain.
- Intent không được dùng để thay thế state machine.

DOMAIN TYPES
------------
- BUSINESS: xử lý nghiệp vụ chính (HR, DBA, Catalog).
- META: chào hỏi, cảm ơn, small talk.
- SYSTEM: routing, fallback, health check.

INTERACTION MODES
-----------------
- STATEFUL: giữ context, có state machine (Catalog).
- COMMAND: nhận input → thực thi → trả kết quả (HR, DBA).
- QA: hỏi–đáp tri thức, không giữ state dài (Knowledge).

REGISTRY LAW
------------
- Registry chỉ chứa metadata.
- Registry KHÔNG khởi tạo handler.
- Registry KHÔNG chứa logic runtime.
- Registry KHÔNG phụ thuộc infrastructure.
- Registry là single source of truth cho domain metadata.

FRONTEND LAW
------------
- Frontend KHÔNG quyết định domain.
- Frontend KHÔNG hard-code intent logic.
- Frontend chỉ render theo metadata registry.
- Frontend không suy luận nghiệp vụ.

HANDLER LAW
-----------
- EntryHandler là điểm vào duy nhất của domain.
- Handler chịu trách nhiệm quản lý state, context, sub-flow.
- Handler không biết domain khác tồn tại.

FORBIDDEN PATTERNS
------------------
- Catalog dùng intent classifier tĩnh.
- Một domain vừa stateful vừa intent-driven.
- Frontend tự route domain.
- Domain tự gọi domain khác.
- Intent thuộc nhiều domain.
- Registry khởi tạo handler.
- Dùng intent_type mơ hồ cho nhiều mục đích.

TEST LAW
--------
- Mỗi domain test độc lập được.
- Router test không cần domain runtime.
- Fail domain boundary test = reject build.

CHANGE RULE
-----------
- Mọi thay đổi vi phạm SYSTEM_CANON đều bị reject.
- Nếu cần phá luật, cập nhật SYSTEM_CANON trước.
- Không vá code để né luật.

AUTHORITY
---------
SYSTEM_CANON là tài liệu tối thượng.
Mọi code, tài liệu, prompt, agent phải tuân thủ.
Mâu thuẫn → SYSTEM_CANON thắng.
