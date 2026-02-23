### Q: về intent trong flow 3 tier có cần ko?

### A :
Vẫn cần, nhưng vai trò của Intent thay đổi tùy theo tầng xử lý (Tier).

Anh có thể hình dung mối quan hệ giữa Intent (Ý định) và State (Trạng thái) như sau:

State: Trả lời cho câu hỏi "Khách hàng đang ở đâu?" (Đang xem xe, đang so sánh...).
Intent: Trả lời cho câu hỏi "Khách hàng muốn làm gì tiếp theo?" (Muốn biết giá, muốn mua...).
Cụ thể trong 3 Tier:

1. Tier 1 (Fast Path - Regex)
Cần Intent cứng: Ở tầng này, chúng ta dùng các mẫu (Pattern) để bắt các Intent xã giao cơ bản (GREETING, BYE, HELP).
Mục đích: Để ngắt luồng sớm, không tốn tiền LLM cho những câu chào hỏi.
2. Tier 2 (Knowledge Path - Semantic FAQ)
Cần Intent "mờ": Tầng này so khớp ngữ nghĩa. User hỏi "Bảo hành thế nào?" -> Hệ thống hiểu Intent là truy vấn thông tin bảo hành và trả về FAQ tương ứng.
Mục đích: Giải quyết các câu hỏi "ngoài lề" (Out-of-flow) mà không làm thay đổi trạng thái của cuộc bán hàng.
3. Tier 3 (Agentic Path - Hybrid Orchestration)
Đây là nơi Intent đóng vai trò "Cầu nối Logic" quan trọng nhất:

Thay vì để AI tự do nhảy từ A đến Z (dễ bị ảo tưởng - hallucination), ta dùng Intent như một bước khai báo ý định.
Quy trình:
LLM nhận diện: "Khách này muốn chốt đơn" -> Gán nhãn INTENT_REQUEST_PAYMENT.
FlowDecisionService
 kiểm tra: "Hợp đồng đã làm chưa? Hàng có sẵn không?".
Nếu thỏa mãn: Cho phép chuyển State sang PURCHASING.
Nếu bỏ Intent ở Tier 3: AI sẽ chỉ dựa vào tên Tool. User nói "Cái này đắt quá" -> AI có thể vô tình gọi tool credit_scoring (tính điểm tín dụng) trong khi user chỉ đang than phiền. Có Intent làm lớp đệm sẽ giúp hệ thống kiểm soát được: "Câu này là INTENT_COMPLAIN_PRICE, không phải INTENT_APPLY_LOAN".

[!TIP] State là cái khung (FSM) bảo vệ bot không đi lạc, còn Intent là cái nhiên liệu để bot xin phép dịch chuyển trong cái khung đó. Anh có thể xem lại INTENT_USAGE_POLICY.md em vừa soạn để thấy các ví dụ cụ thể về việc phân loại này.