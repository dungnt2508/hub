# Cấu trúc : 5 tầng (layer) và 3 ring

### 3 RING (cốt lõi của Clean Architecture - concentric rings)
- Đây là khung nguyên bản. Không thay đổi.

##### Ring 1 – Domain (Inner Circle)
    ```
       Entity
       Value Object
       Domain Event
       Domain Service
       Rule thuần
       Không phụ thuộc framework
       Không phụ thuộc DB
       Không phụ thuộc API
    ```
    
    -  Đây là lõi bất biến.

##### Ring 2 – Application (Use-Case Circle)
        ```
       Use-case
       Orchestrator
       Boundary Input/Output
       Port/Interface
       ```

       Không có HTTP, không có SQL, không có SAP, không có n8n.
       Chỉ định nghĩa interface cần gọi.

##### Ring 3 – Interface + Infrastructure (Outer Circle)
    ```
       Controller
       Presenter
       Repository Implementation
       SQL
       SAP Adapter
       SharePoint Adapter
       n8n Adapter
       LLM Adapter
       Logging
       Auth
       File storage
       Email/Teams Gateway
    ```

Tất cả phụ thuộc vào ring 1–2, nhưng ring 1–2 không phụ thuộc lại.

##### 5 TẦNG            
            ```
                [ Enterprise Layer ]
            Gateway • IAM • Audit • Event Bus
                       ↓
                [ Interface Adapters ]
      API Controllers • SAP Adapter • SharePoint Adapter
      Repo Implementation • Bot Adapter • n8n Adapter
                       ↓
                [ Application Layer ]
       Use Cases • Workflow • Authorization Rules
                       ↓
                 [ Domain Layer ]
    Entities • Domain Services • Domain Events • VO
                       ↓
            [ Infrastructure Layer ]
    DB • Message Broker • Caching • File Storage • Logging
    ```

##### Tại sao lại có thêm 5 TẦNG?

Trong doanh nghiệp thật (ví dụ PNJ), 3-ring không đủ vì cần phân biệt rõ hơn vai trò kỹ thuật và chưa đủ để mô tả phân tầng vận hành.

Do đó kiến trúc cần trải xuống 5 tầng theo khía cạnh kỹ thuật (implementation layering):