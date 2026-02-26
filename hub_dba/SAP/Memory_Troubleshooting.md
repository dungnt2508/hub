# Hướng dẫn Kiểm tra và Xử lý Tràn bộ nhớ (Low Free Memory) trên SAP GUI

Khi nhận được cảnh báo CloudWatch về **"Free Memory < 5%"**, hệ thống đang gặp tình trạng cạn kiệt RAM vật lý. Dưới đây là các bước để kiểm tra và giải phóng bộ nhớ bằng SAP GUI.

## 1. Kiểm tra Tổng quan Hệ thống (OS Level)
Để xác nhận lại thông tin từ CloudWatch và xem tình trạng RAM thực tế trên Server:
- **T-code: ST06** (hoặc **OS07N**)
- **Mục tiêu:** Kiểm tra cột **"Physical Memory"** và **"Free"**. Xem xét lượng **Swap space** đang sử dụng. Nếu Swap cao, hệ thống đang bị chậm do phải ghi dữ liệu RAM xuống đĩa cứng.

## 2. Kiểm tra Bộ nhớ SAP (Buffers & Tune Summary)
- **T-code: ST02**
- **Mục tiêu:** Kiểm tra các thành phần bộ nhớ của SAP (Roll area, Extended Memory, Heap Memory).
- Nhìn vào cột **"Max. use"** và **"In memory"**. Nếu các dòng màu đỏ xuất hiện, nghĩa là các tham số bộ nhớ SAP cần được điều chỉnh (Basis level).

## 3. Tìm kiếm "Kẻ chủ mưu" chiếm dụng RAM
Có 2 cách chính để tìm xem User hoặc Process nào đang ngốn nhiều RAM nhất:

### Cách A: Kiểm tra theo User (SM04 / AL08)
- **T-code: SM04** (Cho instance hiện tại) hoặc **AL08** (Cho toàn hệ thống).
- Trong **SM04**, chọn menu **Layout** -> **Change Layout** -> Thêm cột **"Memory"** vào hiển thị.
- Sắp xếp cột **Memory** giảm dần để tìm User đang chiếm nhiều bộ nhớ nhất.

### Cách B: Kiểm tra Work Processes (SM50 / SM66)
- **T-code: SM50** (Cục bộ) hoặc **SM66** (Toàn hệ thống).
- Quan sát cột **"Memory"**.
- Tìm các Process có trạng thái **"Running"** lâu hoặc đang ở trạng thái **"PRIV"** (Private mode). Trạng thái PRIV thường là nguyên nhân chính gây tràn bộ nhớ vì RAM không được chia sẻ lại cho hệ thống.

## 4. Cách "Kill" Session / Process để giải phóng RAM

> [!WARNING]
> **Thận trọng:** Việc kill session có thể làm mất dữ liệu chưa lưu của người dùng hoặc gây lỗi cho các Batch Job đang chạy. Chỉ thực hiện khi thực sự cần thiết.

### Bước 1: Thông báo (Nếu có thể)
- Trước khi kill, hãy thử liên hệ với User (Dựa trên User ID tìm được ở SM04) để yêu cầu họ thoát T-code hoặc kiểm tra xem họ có đang chạy báo cáo quá nặng không.

### Bước 2: Thực hiện Kill trên SM04 (Dành cho User Session)
1. Truy cập **SM04**.
2. Chọn dòng của User cần xử lý.
3. Trên thanh Menu: **User** -> **Logoff** -> **Local** (hoặc System).

### Bước 3: Thực hiện Kill trên SM50 (Dành cho Work Process)
1. Truy cập **SM50**.
2. Chọn dòng Process đang chiếm nhiều tài nguyên (thường là loại DIA hoặc BTC ở trạng thái PRIV).
3. Trên thanh Menu: **Process** -> **Cancel Without Core** (Hủy process mà không tạo file dump, nhanh và sạch hơn).

---
> [!TIP]
> **Lời khuyên:** Sau khi kill, hãy theo dõi lại **ST06** sau 5-10 phút để xem chỉ số "Free Memory" có tăng lên hay không. Nếu không tăng, có thể vấn đề nằm ở OS hoặc các ứng dụng ngoài SAP chạy trên cùng Server.
