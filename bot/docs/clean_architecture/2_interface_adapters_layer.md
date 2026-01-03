# I. Interface Adapters (Outer Layer – Adapter)
- Lớp này map hệ thống ngoài vào domain
- Adapters cần có:
    ```
    SharePoint Adapter
    (Graph API client, mapping fields → Domain Object)

    SAP Adapter
    (RFC/BAPI/ODATA client)

    SQL Adapter
    (MSSQL, PostgreSQL)

    n8n Adapter
    (Webhook in/out, Trigger, Action Handler)

    Teams Bot Adapter
    (Teams message → Application DTO)

    REST Controller
    (HTTP API)

    Persistence Adapter
    (Repo implementation cho PostgreSQL)
    ```
- Lớp này chứa:
    ```
    Controller
    Repository implementation (SQL)
    External API client (SAP, SharePoint)
    DTO <-> Domain mapping
    ```
# II. giải thích thêm
- Interface Adapters là lớp trung gian giữa thế giới bên ngoài và Use-Case/Application. Nó tồn tại vì dữ liệu bên ngoài không bao giờ đúng định dạng mà nghiệp vụ cần. 
- Lớp này biến đổi, chuyển dạng, cô lập.   
## Bản chất:
### 1. Controller Adapter
```
    Nhận request từ HTTP, Teams, n8n webhook, Graph API callback.
    Nhiệm vụ:
        Parse input.
        Biên dịch thành DTO của Use-Case.
        Không giữ logic nghiệp vụ.
        
        Ví dụ: Teams gửi text rác → Controller chuyển thành:
        NormalizeQueryInputDTO
```

### 2. Presenter Adapter
```
    Biến đổi output của Use-Case thành format người dùng cần.
    HTML table, Adaptive Card, JSON cho frontend.
    Use-Case chỉ trả “dữ liệu thô đã qua nghiệp vụ”, Presenter mới lo chuyện render.        
```

### 3. Repository Adapter
```
    Implement interface Repository mà Domain định nghĩa.
    Domain không biết SQL.
    Adapter cầm SQL/Postgre/SAP/SharePoint, map sang entity.    
```
### 4. External System Adapter
```
    Gói lại mọi hệ thống doanh nghiệp đang dùng:

        SharePoint Adapter (Graph API)
        SAP Adapter (RFC/BAPI/ODATA)
        n8n Adapter (HTTP webhook/API)
        SQL Adapter (legacy DB)
        LLM Adapter (OpenAI/Azure)    

        Ví dụ : Use-Case gọi interface:
            ISharePointPort.getListItems()
            -> Adapter thực thi lệnh gọi hệ thống thật.
```
### 5.Mapper
```
    Ở tầng này bắt buộc có mapper hai chiều:
        external → domain
        domain → external
    Domain không bao giờ nhìn thấy JSON xấu từ SharePoint hoặc SAP.            
```

- Đặc điểm quan trọng:
```
    Không chứa nghiệp vụ.
    Không được gọi Domain trực tiếp qua entity. Chỉ dùng Use-Case.
    Không phụ thuộc framework ở trong.
    Nằm ngoài vòng tròn nhưng vẫn bị chi phối bởi contract từ trong ra.
```

## Vai trò: 
- Cô lập Domain và Application khỏi sự bẩn, sự lộn xộn, sự thay đổi thất thường của hệ thống bên ngoài. 
- Systems thay đổi → sửa Adapter. Domain không chạm. Application không chạm.    