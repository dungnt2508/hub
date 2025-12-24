# I. Application Layer (Use-Case Layer – Orchestration)
- Lớp này cầm Use Case.
- Ví dụ:
```
    CreateTicket
    ApproveChange
    SyncStoreInventory
    GeneratePayroll
    ApplyPromotion
    SubmitRiskReport
```
- Thành phần:
```
    Use-Case Interactors
    Input DTO
    Output DTO
    Mapper
    Transaction Coordinator
```
- Lớp này là nơi API hoặc bot gọi vào.
- Không viết SQL, không gọi HTTP, không biết SharePoint hay SAP.
- Tất cả flow nghiệp vụ nằm ở đây.

# II. Giải thích thêm
- Application Layer là nơi điều phối nghiệp vụ nhưng không sở hữu dữ liệu và không biết kỹ thuật. 
- Nó chỉ biết “phải làm gì”, không biết “làm như thế nào”.

## Vai trò:
### 1. Use-Case Orchestration
    - Một use-case là một hành động nghiệp vụ hoàn chỉnh:
```
        CreateTicket
        SubmitRiskReport
        ApproveChange
        SyncStoreInventory
        GeneratePayroll
        BuildFilteredSharePointQuery
```
    - Use-case cầm luồng:
```
        lấy input DTO
        gọi domain để xử lý rule
        gọi các port để tương tác hệ thống ngoài
        gom kết quả
        trả Output DTO
```
    - Nó là điều phối viên, không phải nơi tính toán.

### 2. Input & Output DTO
    - DTO bảo đảm:
```    
        adapter gửi vào đúng thứ
        presenter nhận ra đúng dữ liệu domain gửi ra
        Use-case không nhận JSON rác từ Teams, SharePoint, SAP.
        Adapter phải chuyển thành DTO trước khi vào.    
```        
### 3. Port Interface (Application Port)        
    - Use-case gọi ra ngoài bằng interface:
    ```
        ISharePointPort
        ISapPort
        IN8NPort
        ILlmPort
        ITicketRepo
        IUserRepo
    ```
    - Application không biết implementation.
    - Adapter layer implement.
    - Infrastructure cấp phụ kiện kỹ thuật.

### 4. Transaction Boundary
    - Use-case là nơi quyết định phạm vi transaction.
    - Ví dụ:
    ```
        Tạo ticket + ghi audit trong cùng transaction
        Update inventory + publish domain event trong cùng transaction    
    ```
    - Use-case mở transaction → domain chạy → adapter chạy → commit.

### 5. Authorization Check
    - Authorization nằm ở đây, không nằm trong Domain.
    - Ví dụ:
    ```
        “User có quyền tạo ticket?”
        “User có quyền duyệt Change Request?”
    ```
    - Use-case kiểm tra qua IAuthzPort.    

### 6. Không chứa logic Domain
    - Use-case không tính toán quy tắc nghiệp vụ.
    - Không viết:
    ```
        SLA rule
        promotion rule
        QC rule
        risk scoring rule
    ```
    - Những cái đó nằm trong domain (entity, domain service).
    - Use-case chỉ gọi domain.
    - Domain trả kết quả.
    - Use-case tiếp tục gọi adapter để thực hiện phần kỹ thuật.    

### 7. Không biết kỹ thuật
    - Use-case không biết:
    ```
        SQL
        HTTP
        SAP BAPI
        SharePoint Graph API
        LLM
        Queue
        Cache
    ```

    - Nó chỉ gọi port và nhận lại entity/value object.        

### 8. Không gọi framework
- Không FastAPI, không NestJS, không ORM, không Teams Bot SDK.
- Đó là phần của adapter layer.    

- Tóm gọn
```
    Application Layer = orchestrator thuần.
    Đại diện cho một use-case thực tế.
    Điều phối domain + adapter.
    Quản lý transaction.
    Kiểm quyền.
    Không tính toán.
    Không biết kỹ thuật.
```

    - Domain làm logic.
    - Adapter làm kỹ thuật.
    - Use-case điều phối cả hai.