# Plan: SAP Monitoring & Preparation for Peak Season

Bản kế hoạch này tập trung vào việc đảm bảo hệ thống SAP hoạt động ổn định khi lượng truy cập (traffic) tăng đột biến trong mùa cao điểm.

## 1. Chuẩn bị (Trước cao điểm)
### Quản lý hạ tầng (Hardware/Infrastructure)
*   **Capacity Check**: Kiểm tra CPU, RAM, Disk I/O hiện tại. Đảm bảo có dư ít nhất 30-40% tài nguyên dự phòng.
*   **Scale-out/Scale-up**: Nếu chạy trên Cloud (AWS, Azure, GCP), chuẩn bị kịch bản nâng cấp Instance hoặc thêm Application Server.
*   **Network Check**: Kiểm tra băng thông đường truyền và cấu hình Load Balancer (SAP Web Dispatcher).

### Tối ưu hóa hệ thống SAP (Application Tuning)
*   **Housekeeping (Dọn dẹp)**: 
    *   **Spool (`SP01`)**: Xóa các spool cũ không còn giá trị (dùng report `RSPO0041`).
    *   **Job Logs (`SM37`)**: Xóa log các job đã hoàn thành từ lâu (dùng report `RSBTCDEL2`).
    *   **IDocs (`WE02/WE05`)**: Archive hoặc xóa các IDoc lỗi/cũ (dùng report `RSEOUT00` cho Outbound).
    *   **Dumps (`ST22`)**: Kiểm tra và dọn dẹp các Short Dumps quá cũ.
*   **Work Process Configuration (`RZ10`)**: 
    *   Tăng số lượng `rdisp/wp_no_dia` (Dialog) để tăng khả năng phục vụ user đồng thời.
    *   Kiểm tra `rdisp/wp_no_upd` để tránh nghẽn khi lưu dữ liệu hàng loạt.
*   **Memory Parameters**: 
    *   `abap/heap_area_total`: Tổng bộ nhớ Heap cho toàn instance.
    *   `ztta/roll_extension`: Giới hạn Extended Memory cho mỗi user session.
    *   Theo dõi `ST02` để đảm bảo tỉ lệ **Overflow** của các Buffer là nhỏ nhất.

## 2. Giám sát thời gian thực & Các chỉ số quan trọng

Dưới đây là chi tiết các T-code và những thông tin "sống còn" bạn cần nhìn vào khi traffic tăng cao:

### A. Giám sát người dùng & Phiên làm việc
*   **AL08 (Toàn hệ thống) / SM04 (Local server)**:
    *   **Mục đích**: Biết được "độ nóng" của hệ thống qua số lượng user.
    *   **Cột quan trọng**:
        *   `User`: Định danh người dùng.
        *   `Application (T-code)`: Biết user đang tập trung ở nghiệp vụ nào (VD: Đang dồn lứa tạo đơn hàng `VA01`).
        *   `Memory`: Nếu một user chiếm vài trăm MB, có thể họ đang chạy báo cáo quá nặng.
        *   `Time`: Thời gian login. Nếu user treo quá lâu mà không thoát, cần xem xét kill session.

### B. Giám sát Hiệu năng xử lý (Work Processes)
*   **SM50 (Local) / SM66 (Global)**:
    *   **Mục đích**: Xem các "cánh tay" của SAP (Work Processes) có đang bị kẹt hay không.
    *   **Cột quan trọng**:
        *   `Type`: `DIA` (Dialog - xử lý cho user), `UPD` (Update - lưu DB), `BGD` (Background - chạy ngầm).
        *   `Status`: Nếu nhiều process ở trạng thái **Running** quá lâu hoặc **Waiting** nhưng cột `Reason` là **Priv** (chiếm bộ nhớ riêng), hệ thống sẽ chậm.
        *   `CPU Time`: Process nào có CPU time tăng đột biến là dấu hiệu của chương trình bị lặp vô hạn hoặc truy vấn DB kém.
        *   `Action/Table`: Tên bảng dữ liệu đang bị truy vấn (giúp phát hiện nghẽn ở Table nào).

### C. Giám sát Hạ tầng & Bộ nhớ
*   **ST06 / OS07N**:
    *   **Mục đích**: Kiểm tra "sức khỏe" Server vật lý/ảo.
    *   **Thông số quan trọng**:
        *   `CPU Utilization`: Nếu > 80% liên tục là báo động đỏ.
        *   `Load Average`: Số lượng tiến trình đang đợi CPU.
        *   `Free RAM` & `Swap`: Nếu SAP phải dùng đến Swap (bộ nhớ ảo trên ổ cứng), tốc độ sẽ cực chậm.
*   **ST02 (Setup/Tune Summary)**:
    *   **Mục đích**: Kiểm tra các bộ nhớ đệm (Buffers).
    *   **Cột quan trọng**:
        *   `Hit Ratio`: Nên > 95%. Nếu thấp, SAP phải đọc từ DB nhiều hơn -> chậm.
        *   `Swaps`: Nếu số lượng Swap lớn, Buffer đó đang quá nhỏ, cần tăng size.

### D. Giám sát Cơ sở dữ liệu & Nghẽn (Bottlenecks)
*   **SM12 (Lock Entries)**:
    *   **Mục đích**: Kiểm tra xem có ai đang "xí phần" dữ liệu quá lâu không.
    *   **Cột quan trọng**: `Table`, `Lock Argument` (ID bản ghi), `Time`. Nếu một bản ghi bị lock cả tiếng đồng hồ, các user khác sẽ bị treo khi sửa bản ghi đó.
*   **SM13 (Update Requests)**:
    *   **Mục đích**: Đảm bảo dữ liệu đã nhấn "Save" được ghi vào DB thành công.
    *   **Status**: Nếu thấy status `Error` hoặc `V1/V2 canceled`, nghĩa là giao dịch của user bị mất dữ liệu, cần xử lý ngay.

### E. Phân tích chi tiết (Workload Analysis)
*   **ST03N / STAD**:
    *   **Mục đích**: Xem lại lịch sử hoặc phân tích sâu nguyên nhân chậm.
    *   **Chỉ số quan trọng**:
        *   `Response Time`: Thời gian phản hồi trung bình (Nên < 1s cho Dialog).
        *   `Wait Time`: Thời gian đợi process. Nếu cao -> thiếu Work Process.
        *   `DB Time`: Nếu cao -> Query DB chậm hoặc thiếu Index.

## 3. Kịch bản ứng phó (Incident Response)

### A. Xóa session treo hoặc user chiếm tài nguyên (SM04 / SM50)
Trong mùa cao điểm, nếu một user chạy report quá nặng gây treo server, bạn cần xử lý nhanh:
*   **Cách 1 (SM04)**: 
    1. Chọn User cần xóa. 
    2. Menu chọn `User` -> `Log off` -> `System-wide` (để kick user khỏi toàn bộ hệ thống) hoặc `Local` (chỉ server hiện tại).
*   **Cách 2 (SM50/SM66)**: Nếu biết chính xác Work Process đang bị treo:
    1. Chọn dòng Process đó.
    2. Menu chọn `Process` -> `Cancel` -> `With Core` (nếu cần log để debug sau) hoặc `Without Core` (xóa nhanh ngay lập tức).

### B. Restart nhanh Service / Instance
Khi hệ thống bị nghẽn nghiêm trọng không thể thao tác trên GUI:
*   **Sử dụng `sapcontrol` (Dòng lệnh OS - Linux/Unix/Windows)**:
    *   *Kiểm tra trạng thái*: `sapcontrol -nr [Instance_Number] -function GetProcessList`
    *   *Restart Instance*: `sapcontrol -nr [Instance_Number] -function RestartInstance`
    *   *Dừng khẩn cấp*: `sapcontrol -nr [Instance_Number] -function Stop`
*   **Sử dụng SAP Management Console (MMC - Windows)**:
    *   Mở SAP MMC, chuột phải vào Instance bị treo và chọn **Restart**.

### C. Quản lý Batch Jobs (SM37)
*   Nếu hệ thống quá tải CPU, hãy tìm các Job `Active` có thời gian chạy quá lâu.
*   Chọn Job -> `Job` -> `Cancel Active Job`. Chuyển các job này sang chạy vào khung giờ đêm.

## 4. Kế hoạch xác minh
*   **Load Testing**: Thực hiện stress test hệ thống trước khi vào mùa cao điểm.
*   **Alerting Setup**: Cấu hình cảnh báo tự động (Email/Telegram) qua SAP Solution Manager hoặc các giải pháp bên thứ 3.
