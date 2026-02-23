# Trang Integrations (Tích hợp) đóng vai trò là "Cổng kết nối" giữa bộ não AI của bạn và thế giới bên ngoài. Trong kiến trúc của IRIS Hub v4, trang này có 2 nhiệm vụ chiến lược:

## 1. Kết nối đa kênh (Omnichannel - Đầu vào)
Đây là nơi bạn cấu hình để con Bot có thể xuất hiện ở khắp mọi nơi:

Webchat Widget: Nhúng vào website của bạn.
Zalo OA / Facebook Messenger: Kết nối qua các Social API để bot trả lời khách hàng trên mạng xã hội.
Custom API / SDK: Dành cho các lập trình viên muốn nhúng sức mạnh của IRIS Hub vào ứng dụng riêng.
## 2. Kết nối công cụ (External Tools - Đầu ra)
Đây là phần liên quan trực tiếp đến Capability: AUTOMATE mà chúng ta đã thảo luận.

    ### Webhook (n8n, Make, Zapier): Khi AI hiểu rằng khách hàng muốn "Đặt hàng" hoặc "Tra cứu vận đơn", nó sẽ gọi đến các Webhook được cấu hình tại đây để kích hoạt quy trình tự động ở các hệ thống khác.

    ### Enterprise Security: Trang này quản lý các Keys (mã bảo mật) để đảm bảo mọi tin nhắn ra/vào đều được xác thực an toàn.

## Tại sao nó quan trọng?
Nếu Bots Page là nơi bạn tạo ra "Bộ não", thì Integrations Page là nơi bạn gắn "Chân tay" và "Các giác quan" cho nó.

Không có Integrations, Bot chỉ có thể chat trên giao diện test.
Có Integrations, Bot có thể tự động tạo đơn hàng trên KiotViet, gửi thông báo vào Slack, hoặc tự động trả lời bình luận trên Fanpage.
Hiện tại, trang này đang ở mức Layout (Giao diện mẫu). Trong các Sprint tiếp theo, chúng ta sẽ bắt đầu tích hợp các API để bạn có thể nhập URL Webhook thật hoặc cấu hình Token của Zalo/Facebook ngay trên giao diện này.


# Dựa trên tiến độ hiện tại của dự án, tôi không khuyến nghị build trang Integrations ngay lúc này. Thay vào đó, tôi đề xuất bạn tập trung vào trang Knowledge Base / Catalog hoặc Agent Monitor.

## Lý do của tôi như sau:

1. Tại sao chưa nên build Integrations lúc này?
Integrations (Webchat, Zalo,...) là phần "vỏ" bên ngoài. Hiện tại chúng ta đã có Giao diện Chat để test Bot rồi. Nếu build Integrations ngay, bạn sẽ có một con Bot có thể nhúng vào Website, nhưng bên trong "bộ não" của nó vẫn chưa có dữ liệu thật (Sản phẩm, FAQ thật) để trả lời.

2. Khuyến nghị 1: Build Knowledge Base / Catalog (Mức ưu tiên: Cao nhất)
Đây là "nhiên liệu" cho con Bot. Chúng ta vừa làm xong phần Capabilities (SEARCH, RECOMMEND).

Nếu không có trang này, các tính năng Search/Recommend của bạn vẫn chỉ đang chạy trên dữ liệu giả (Mock data).
Mục tiêu: Build trang này để bạn có thể tải lên danh sách sản phẩm thật, câu hỏi thường gặp thật. Khi đó, con Bot sẽ lập tức trở nên "thông minh" một cách thực tế.
3. Khuyến nghị 2: Build Agent Monitor - Realtime Audit (Mức ưu tiên: Cao)
Nếu bạn muốn thấy sự "Kỳ diệu" của Tier 3 (Agentic), thì đây là trang quan trọng nhất.

Trang này sẽ hiển thị tường tận quá trình AI suy nghĩ: "Người dùng hỏi X -> Tôi nghĩ là cần dùng tool Tìm Kiếm -> Tôi lấy được kết quả Y -> Tôi trả lời khách hàng Z".
Build trang này giúp bạn Debug (sửa lỗi) và tối ưu con Bot cực nhanh vì bạn nhìn thấy "nội tâm" của AI.

## Lời khuyên của tôi:
Bạn nên build trang Knowledge Base / Catalog trước.

Nó sẽ hoàn thiện mảnh ghép dữ liệu (Data Layer).
Nó trực tiếp chứng minh giá trị của các 
Capabilities mà chúng ta vừa vất vả triển khai ở Bot Page.