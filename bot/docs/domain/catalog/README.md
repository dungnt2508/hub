CATALOG DOMAIN
==============

Domain tìm kiếm và tra cứu sản phẩm, mua sắm trực tuyến.

DOMAIN PURPOSE
--------------

Phục vụ exploration, không phải command execution.

Hỗ trợ:
- Tìm kiếm sản phẩm
- Xem thông tin sản phẩm
- So sánh sản phẩm
- Kiểm tra giá, tồn kho
- Thêm vào giỏ hàng
- Đặt hàng

DOMAIN TYPE
-----------

BUSINESS

STATEFUL domain.

INTERACTION MODE
----------------

EXPLORE

Giữ context, có state machine.

Mọi hành vi (browse, filter, refine, compare) do state machine nội bộ xử lý.

ENTRY POINT
-----------

CatalogEntryHandler.handle()

Router gửi DomainRequest với intent từ intent_registry.yaml.

EntryHandler map intent → use case → execute.

ALLOWED RESPONSIBILITIES
------------------------

- Xử lý intent từ router.
- Map intent → use case.
- Thực thi use case.
- Quản lý state machine nội bộ.
- Xử lý browse, filter, refine, compare.
- Trả DomainResponse với result.

FORBIDDEN RESPONSIBILITIES
--------------------------

- Expose intent list tĩnh.
- Dùng intent classifier để điều hướng nội bộ.
- Gọi trực tiếp domain khác.
- Quyết định routing domain.
- Phụ thuộc vào frontend.
- Xử lý logic nghiệp vụ ngoài Catalog.

CATALOG CANON
-------------

Catalog là STATEFUL domain.

Catalog KHÔNG expose intent list.

Catalog KHÔNG intent tĩnh.

Catalog KHÔNG dùng intent classifier để điều hướng nội bộ.

Mọi hành vi catalog do state machine nội bộ xử lý.

Catalog chỉ emit signal khi cần rời domain (ví dụ: mua hàng).

EXIT CONDITIONS
---------------

Domain trả response khi:
- Use case thực thi xong (SUCCESS).
- Use case lỗi (ERROR).
- Thiếu thông tin (NEED_MORE_INFO).

Domain emit signal khi cần rời domain:
- Mua hàng → signal để chuyển domain thanh toán.
- Hỗ trợ → signal để chuyển domain support.

Domain không tự chuyển domain.

User muốn chuyển domain → gửi message mới → Router xử lý.

STATE MACHINE
-------------

Catalog dùng state machine để quản lý:
- Browse state: duyệt sản phẩm
- Filter state: lọc sản phẩm
- Compare state: so sánh sản phẩm
- Cart state: quản lý giỏ hàng
- Checkout state: thanh toán

State machine xử lý chuyển đổi giữa các state.

Intent chỉ là trigger, không phải điều hướng nội bộ.
