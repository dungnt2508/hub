# I. Enterprise Architecture Layer (Top Layer – Cross-Domain)
    - Thành phần:
    ```
    API Gateway
    Auth / Identity / RBAC
    Audit Trail Engine
    Event Bus (Kafka/RabbitMQ)
    Notification Engine (Email/Teams/SMS/Webhook)
    Central Logging & Monitoring
    Compliance/Policy Engine
    ```
    Layer này đảm bảo toàn bộ service trong doanh nghiệp vận hành theo chuẩn chung.


# II. Giải thích thêm và tại sao gọi là cross-cutting

- Enterprise Architecture Layer là tầng cao nhất vì nó không thuộc bất kỳ module nghiệp vụ nào, nhưng mọi module đều phải đi xuyên qua nó. 
- Đó là lý do gọi là cross-cutting: nó cắt ngang toàn bộ hệ thống, tác động lên tất cả domain, tất cả service, tất cả API.

    Không phải nghiệp vụ.
    Không thuộc domain cụ thể.
    Không được bỏ qua.
    Không được implement lặp lại ở từng service.

- Bản chất cross-cutting của tầng này:
    ```
        Auth / IAM / RBAC
            Toàn bộ service đều phải qua xác thực và phân quyền.
            Ticket-Service cũng dùng.
            HR-Service cũng dùng.
            Retail-Service cũng dùng.
            Không ai được implement lại permission riêng.
            → cross-cutting.

        Audit Trail
            Mỗi lần tạo Ticket, HR update nhân viên, SAP đồng bộ kho — đều phải log.
            Log không thể đặt trong từng domain vì gây rối domain.
            → cross-cutting bắt buộc.

        API Gateway
            Mọi request từ bot, web, n8n đều đi qua.
            Không domain nào vượt qua gateway.
            → cross-cutting.

        Event Bus (Kafka/Rabbit)
            Domain phát ra event. Service khác nghe event.
            Bus nằm ngoài domain.
            → cross-cutting.

        Observability (logging, tracing, metrics)
            Không thể cho từng domain tự log theo kiểu riêng.
            → cross-cutting.

        Policy Engine / Compliance
            Data retention, masking, classification.
            Áp cho tất cả service.
            → cross-cutting.

        Rate Limit / Throttle / Gateway Cache
            Bảo vệ toàn bộ system.
            → cross-cutting.
        ```

- Tóm lại:
    ```
        Domain giải quyết nghiệp vụ cục bộ.
        Application orchestrate use-case cụ thể.
        Adapters kết nối hệ thống ngoài.
        Infrastructure cung cấp kỹ thuật chi tiết.
        Enterprise Layer xử lý mọi thứ mà TẤT CẢ các domain phụ thuộc vào nhưng không thuộc domain nào cả.
    ```

    Nó cắt theo chiều ngang → cross-cutting.