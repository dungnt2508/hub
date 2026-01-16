REGISTRY
========

Registry là metadata layer cho domain.

NHIỆM VỤ
---------

Registry chỉ chứa metadata.

Registry KHÔNG khởi tạo handler.

Registry KHÔNG chứa logic runtime.

Registry KHÔNG phụ thuộc infrastructure.

Registry là single source of truth cho domain metadata.

CẤU TRÚC
--------

Registry chứa:
- DomainSpec: tên, mô tả, domain type, interaction mode.
- IntentSpec: chỉ cho OPERATION domain.

Registry không chứa:
- Handler instances.
- Runtime state.
- Business logic.

PHỤC VỤ
--------

Registry phục vụ:
- Frontend: lấy metadata để render UI.
- Router: lấy danh sách domain để routing.

Registry không phục vụ:
- Domain handler runtime.
- Business logic execution.

DOMAIN TYPES TRONG REGISTRY
---------------------------

OPERATION domain:
- Có intent list.
- IntentSpec cho mỗi intent.

STATEFUL domain:
- Không có intent list.
- Metadata chỉ mô tả domain.

KNOWLEDGE domain:
- Không có intent list.
- Xử lý query động.

META domain:
- Không có intent list.
- Xử lý task động.

API
---

get_domain(domain_name) → DomainSpec
get_all_domains() → List[DomainSpec]
get_all_intents() → List[IntentSpec] (chỉ OPERATION)
get_intents_by_domain(domain_name) → List[IntentSpec]

LƯU Ý
-----

Registry không biết handler tồn tại.

Handler được khởi tạo bởi DomainDispatcher tại runtime.

Registry và Handler hoàn toàn tách biệt.
