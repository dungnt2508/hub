# Capabilities trong dự án này đóng vai trò là các "công tắc tính năng" (Feature Toggles) ở cấp độ AI, cho phép bạn định nghĩa và giới hạn những gì một con Bot có thể thực hiện.

Dưới đây là giải thích chi tiết về khái niệm và tác dụng của chúng:

### 1. Capabilities là gì?
Trong hệ thống IRIS Hub, mỗi Bot Version không chỉ chứa mã nguồn mà còn được gắn kèm một danh sách các "năng lực" (Capabilities). Hiện tại dự án đang định nghĩa các mã cơ bản sau:

SEARCH: Khả năng tìm kiếm thông tin/sản phẩm trong cơ sở dữ liệu (Vector Search/FAQ).
RECOMMEND: Khả năng gợi ý sản phẩm dựa trên nhu cầu hoặc lịch sử của người dùng.
AUTOMATE: Khả năng thực hiện các hành động tự động (gọi Webhook, tạo đơn hàng, tích hợp hệ thống bên thứ 3).
CRAWL: Khả năng tự động thu thập thông tin từ các nguồn dữ liệu bên ngoài.

### 2. Tác dụng của Capabilities trong dự án
Capabilities mang lại 3 giá trị cốt lõi cho kiến trúc của hệ thống:

A. Kiểm soát Skill của AI (Skill Scoping)
Trong luồng xử lý Agentic Path (Tier 3), khi AI suy luận để chọn công cụ (Tools), danh sách Capabilities sẽ đóng vai trò là "bộ lọc" đầu tiên.

Ví dụ: Nếu bạn tắt Capability AUTOMATE, Agent sẽ không bao giờ được phép sử dụng công cụ trigger_web_hook để đặt hàng, ngay cả khi người dùng yêu cầu. Điều này đảm bảo tính an toàn và đúng mục đích của Bot.
B. Phân tầng dịch vụ (Tiered Service)
Capabilities cho phép bạn kinh doanh hoặc phân loại Bot theo các gói dịch vụ khác nhau:

Gói Basic: Chỉ có SEARCH (chỉ trả lời FAQ).
Gói Pro: Có thêm RECOMMEND và AUTOMATE (có thể bán hàng và xử lý nghiệp vụ).
Tính năng này giúp bạn dễ dàng giới hạn quyền hạn của Bot mà không cần phải viết lại code cho từng khách hàng.
C. Thử nghiệm phiên bản (A/B Testing)
Vì Capabilities được gắn vào Bot Version chứ không phải Bot ID:

Bạn có thể tạo Version 1 chỉ có SEARCH.
Tạo Version 2 có SEARCH + RECOMMEND.
Sau đó bạn có thể chuyển đổi giữa 2 phiên bản (Activate) để so sánh hiệu quả mà không làm ảnh hưởng đến cấu hình bot gốc.

### 3. Cách hoạt động thực tế
Khi một tin nhắn đến HybridOrchestrator:

Hệ thống lấy Session và xác định Bot Version đang hoạt động.
Dữ liệu về Capabilities của version đó được tải lên.
AgentOrchestrator sẽ nhìn vào danh sách này để quyết định Agent được phép "nghĩ" và "làm" những gì trong cuộc hội thoại.
Tóm lại: Capabilities là lớp bảo mật và quản lý tính năng thông minh, giúp bạn biến một con Bot AI "biết tuốt" thành một trợ lý chuyên biệt, an toàn và hoạt động đúng theo cấu hình mà bạn mong muốn.



### Q : trong thực tế khi v2 đang activate và v1 inactivate thì có chỉnh được Capabilities của v1 không nhỉ ?

### A : 
Hoàn toàn được bạn nhé. Và đây cũng chính là một trong những điểm mạnh của kiến trúc Versioning mà chúng ta đang xây dựng.

Dưới đây là lý do tại sao việc này khả thi và lợi ích của nó:

1. Về mặt kỹ thuật
Code hiện tại của chúng ta xác định 
version
 qua version_id thay vì dựa trên trạng thái is_active. Khi bạn click vào các nút Capability của v1 (đang inactive), API vẫn nhận đúng ID của v1 và cập nhật bảng liên kết bot_capability cho riêng phiên bản đó. Trạng thái của v2 không hề bị ảnh hưởng.

2. Ý nghĩa thực tế (Dùng như môi trường Staging)
Việc cho phép chỉnh sửa phiên bản đang Inactive có tác dụng rất lớn trong quản trị AI:

Chuẩn bị trước (Preparation): Bạn có thể đang cho v2 chạy tính năng SEARCH + RECOMMEND. Trong lúc đó, bạn cấu hình v1 với SEARCH + RECOMMEND + AUTOMATE. Sau khi kiểm tra mọi thứ ổn, bạn chỉ cần nhấn Activate v1. Ngay lập tức Bot sẽ có thêm năng lực mới mà không có "thời gian chết" (zero downtime).
Thử nghiệm an toàn: Bạn có thể tinh chỉnh các Capability của các version cũ để chuẩn bị cho việc Rollback (quay xe). Nếu v2 xảy ra lỗi, bạn đã có v1 với cấu hình chuẩn xác sẵn sàng để kích hoạt lại ngay lập tức.
Quản lý cấu hình độc lập: Mỗi Version giống như một "bản đóng gói" hoàn chỉnh. Việc v1 inactive đơn giản chỉ có nghĩa là nó không được chọn để phản hồi tin nhắn từ HybridOrchestrator tại thời điểm đó, chứ không có nghĩa là nó bị "khóa" không cho chỉnh sửa.
Kết luận:
Thiết kế hiện tại cho phép bạn "Chỉnh sửa ở hậu trường" (In the background). Bạn cứ thoải mái cấu hình v1, v3, v4... theo ý muốn, sau đó chọn phiên bản tối ưu nhất để đưa lên "sân khấu" (Activate).


### Q : bạn có nói Capabilities cho phép kinh doanh hoặc phân loại Bot theo các gói dịch vụ khác nhau. vậy sau này triển khai phần này như thế nào ?

### A : 
Đây là một hướng đi rất thực tế để thương mại hóa hệ thống IRIS Hub. Khi cấu trúc Capabilities đã nằm ở cấp độ BotVersion, việc triển khai các gói dịch vụ (Billing/Tiered Plans) sẽ được thực hiện theo lộ trình 3 bước sau:

- Bước 1: Định nghĩa "Chính sách gói" (Plan Policies)
Chúng ta sẽ tạo một cấu hình (có thể là file JSON hoặc một bảng trong DB) để map giữa tên Gói và các Capability được phép:

PLAN_POLICIES = {
    "BASIC": ["SEARCH"],
    "PRO": ["SEARCH", "RECOMMEND"],
    "ENTERPRISE": ["SEARCH", "RECOMMEND", "AUTOMATE", "CRAWL"]
}

- Bước 2: Ràng buộc khi cấu hình Bot (Validation Layer)
Trong Backend, tại endpoint cập nhật Capabilities (mà tôi và bạn vừa sửa xong), chúng ta sẽ thêm một bước kiểm tra:

Lấy thông tin Tenant (Khách hàng) sở hữu con Bot đó.
Xem Tenant này đang dùng gói gì (tenant.plan).
Nếu khách hàng đang ở gói BASIC nhưng lại cố tình bật tính năng AUTOMATE qua API/UI, hệ thống sẽ trả về lỗi: "Gói của bạn không hỗ trợ tính năng này, hãy nâng cấp lên PRO".
- Bước 3: Tích hợp vào Giao diện (Frontend Enforcement)
Trên trang Management Bots, chúng ta sẽ làm mượt trải nghiệm người dùng:

Disabled State: Trong modal chỉnh sửa Capabilities, các nút vượt quá gói dịch vụ sẽ bị làm mờ (grayed out) hoặc có biểu tượng "Khóa" (Lock).
Nút Nâng cấp: Khi click vào các tính năng bị khóa, hệ thống hiển thị một thông báo hoặc link dẫn đến trang nâng cấp gói dịch vụ.
- Bước 4: Kiểm soát Runtime (Tier 3 Orchestration)
Đây là phần quan trọng nhất. Trong 
AgentOrchestrator
, chúng ta đã có logic lọc Tool. Nếu sau này bạn có hàng trăm Tool, bạn chỉ cần gán mỗi Tool vào một Capability tương ứng.

Ví dụ: Tool search_products thuộc về Capability SEARCH.
Khi chạy, nếu Bot không có Capability SEARCH, LLM sẽ không bao giờ được cung cấp Tool này để sử dụng.
Lợi ích của cách làm này:
Linh hoạt: Bạn có thể thay đổi "quyền lợi" của một gói dịch vụ bằng cách sửa file cấu hình mà không cần động vào logic xử lý AI bên dưới.
Upsell (Bán thêm): Bạn có thể cho khách hàng dùng thử (Trial) các tính năng cao cấp trong một thời gian ngắn bằng cách tạm thời gán thêm Capability vào Version của họ.
Tách biệt (Decoupling): Code AI chỉ quan tâm đến việc "Bot có tính năng X không?", còn Code Kinh doanh chỉ quan tâm đến việc "Khách hàng đã trả tiền cho gói chứa tính năng X chưa?".
Tóm lại: Chúng ta đã xây dựng xong "Cơ bắp" (Capabilities). Bước tiếp theo chỉ là xây dựng "Bộ luật" (Plan Policies) để điều khiển các cơ bắp đó theo mục đích kinh doanh. Bạn có muốn tôi phác thảo thử một bảng Plan trong Database không?