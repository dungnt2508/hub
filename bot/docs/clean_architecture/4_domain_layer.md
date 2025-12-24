# I. Domain Layer (Inner Circle – Không phụ thuộc gì)
- Đây là “linh hồn” của Clean Architecture.
- Trong doanh nghiệp(ví dụ PNJ) Domain Layer tách thành các bounded context:

### Operation Domain
```
    Ticket
    Incident
    Change
    Asset
    Access
```
### Retail Domain
```
    Store
    Sales
    Promotion
    Inventory
```
### Manufacturing Domain
```
    Manufacturing Order
    QC
    Logistics
    Finance Domain
    Budget
    Invoice
    Cost
```
### HR Domain
```
    Employee
    Attendance
    Payroll
    Leave
```
### Compliance Domain
```
    Policy
    Audit
    Risk Tracking
```

- Tại Domain Layer chỉ có:
```
    Entities
    Value Objects
    Domain Events
    Domain Services (logic thuần)
    Repository Interface (chưa có DB)
    Không framework, không HTTP, không SharePoint, không SAP.
```

# II. Giải thích thêm
- Domain Layer là lõi của toàn bộ kiến trúc. Nếu các tầng khác sập, Domain vẫn đứng vững. Nếu PNJ đổi SAP, bỏ SharePoint, thay n8n bằng Camunda, thay Teams bằng Slack — Domain không thay đổi một dòng. 
- Đó là mục tiêu.
- Không có tầng nào được “tinh khiết” như Domain.

# 1. Domain chứa cái gì?
### Entities (thực thể nghiệp vụ)
```
    - Thứ có identity rõ ràng:
        Ticket
        RiskReport
        ChangeRequest
        Store
        InventoryItem
        Employee
        ManufacturingOrder
    - Entity mang theo:
        trạng thái
        invariants
        rule không được phá
        hành vi thuần
    - Ví dụ Ticket entity tự biết:
            ticket.assignTo(user)
            ticket.resolve()
            ticket.addComment(...)
    - Không phải controller quyết định hành vi.
```

### Value Objects
- Giá trị bất biến, không có identity:
- VD :
```
    Email
    Phone
    Money
    Quantity
    Percentage
    TimeRange
    SKU
    - Nếu đổi email → thành VO mới, không sửa VO cũ.
```
### Domain Services
- Logic nghiệp vụ lớn không thuộc một entity duy nhất
- VD:
```
    tính SLA
    apply promotion rule
    risk scoring
    inventory allocation
```
- Domain Service không biết DB, không gọi API, không biết adapter.

### Domain Events
- Sự kiện phát sinh từ nghiệp vụ:
- VD:
```
    TicketCreated
    InventoryUpdated
    RiskReportSubmitted
    EmployeeOnboarded
```
- Không chứa kỹ thuật.
- Không publish ra Kafka ở Domain. Domain chỉ tạo event. Adapter mới publish.

## 2. Domain không chứa gì?
- Không HTTP
    Không FastAPI, không request/response.
- Không DB
    Không SQL, không ORM, không transaction, không repository implementation.
- Không logic UI
    Không HTML, không Teams card.
- Không gọi hệ thống ngoài
    Không SharePoint, không SAP, không n8n.
- Không biết DTO
    DTO thuộc application layer. Domain làm việc bằng entity/value object.        

## 3. Domain chỉ phụ thuộc chính nó
- Không import từ application, adapter, infrastructure.
- Các layer vòng ngoài được phép phụ thuộc Domain.
- Domain không được phụ thuộc ngược lại.
- Domain là lõi bất biến.
## 4. Ví dụ từ bối cảnh PNJ
### Ticket Entity (PNJ Operation Hub)
```
class Ticket:
    id
    title
    description
    status
    assignee
    createdAt
    updatedAt
```
- Logic trong entity:
```
    close()
    assignTo()
    addComment()
    reopen()
```
- Không có SQL, không có HTTP.
### Inventory Value Object (Retail Hub)
```
class Quantity:
    value
    unit

```
- Logic VO:
```
- tự validate
- không được < 0
```
### Risk Assessment Domain Service (Compliance Hub)
```
score = RiskScoringService.calculate(model)
```
- Sử dụng rule thuần, không gọi DB.
# 5. Domain không chạy một mình
- Domain không tự kích hoạt use-case, không gọi external, không gửi email.
- Nó chỉ biết rule.
- Use-case orchestrate.
- Adapter thực thi công việc thật.
# 6. Lợi ích tại PNJ
### 1. Hệ thống cũ thay đổi không tác động nghiệp vụ
    SharePoint đổi Graph API → sửa adapter
    SAP đổi endpoint → sửa adapter
    Domain không đụng.
### 2. Đổi UI không ảnh hưởng nghiệp vụ
    Teams → Web → Mobile → POS
    Domain giữ nguyên.
### 3. Thêm LLM không ảnh hưởng nghiệp vụ
    LLM chỉ nằm ở adapter.
    Domain không chứa AI logic.
### 4. Tách logic nghiệp vụ khỏi rác kỹ thuật
    Không dính JSON bẩn từ SharePoint.
    Không dính text bẩn của Teams.
    Không dính lỗi SAP.
    Domain nhận thứ sạch, trả thứ sạch.
# 7. Chốt
- Domain là nơi duy nhất bạn “định nghĩa PNJ hoạt động như thế nào”.
- Tất cả thứ còn lại chỉ là cách để thực thi điều đó.
# Q&A
- Q: 
```
ví dụ như object ticket tôi thêm vào một thuộc tính mới và sẽ sinh ra hành vi mới thì domain thay đổi mà nhỉ ?
```
- A : 
```
Đúng. Domain thay đổi. Và đó là điểm cốt lõi: Domain chỉ thay đổi khi nghiệp vụ thực sự thay đổi.
Phần còn lại của hệ thống không được phép thay đổi khi bạn thêm thuộc tính hoặc hành vi mới.
Cơ chế đúng:
- Bạn thêm thuộc tính mới vào Ticket → Domain Layer thay đổi.
- Bạn thêm hành vi mới (method) vào Ticket → Domain Layer thay đổi.
- Use-case gọi vào hành vi mới → Application Layer chỉ chỉnh lại orchestrate, không chỉnh logic.
- Adapter (SQL/SharePoint/SAP/HTTP) không thay đổi trừ khi bạn cần map IO mới.
- Enterprise Layer tuyệt đối không thay đổi.

Điểm quan trọng:
- Domain thay đổi là bản chất.
- Không được để thay đổi Domain kéo theo thay đổi ở 4 tầng còn lại.
- Điều bạn tránh là logic nghiệp vụ nằm sai chỗ, khiến thêm một field phải sửa 10 nơi.
- Khi Domain thay đổi, bạn chỉ sửa:
        Entity
        Value Object
        Domain Service
        Domain Event
        
- Không sửa framework, không sửa infra, không sửa controller, không sửa adapter trừ khi ngoại lệ liên quan dữ liệu.
- Tóm lại: Domain thay đổi duy nhất khi nghiệp vụ thay đổi. Các tầng khác không được thay đổi theo.
```
