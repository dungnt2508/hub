Dựa trên hình ảnh bạn gửi, đây là cảnh báo ổ đĩa F: (nhãn LogFile) sắp hết dung lượng trên hai server SRVSQL01 (< 1%) và SRVSQL02 (4%).

Ổ đĩa này thường chứa các file Transaction Log (.ldf) của SQL Server. Khi ổ đĩa chứa Log bị đầy, SQL Server sẽ không thể thực hiện các tác vụ ghi (Insert/Update/Delete) và database có thể bị rơi vào trạng thái Read-Only hoặc In Recovery.

Dưới đây là các query quan trọng để bạn kiểm tra nguyên nhân và xử lý:

1. Kiểm tra dung lượng Log tổng thể (Tương thích mọi phiên bản SQL 2005+)
-- Cách này lấy dung lượng file vật lý trên ổ đĩa.
SELECT 
    d.name AS DatabaseName,
    d.recovery_model_desc AS RecoveryModel,
    d.log_reuse_wait_desc AS LogReuseWaitReason,
    CAST(SUM(CASE WHEN f.type_desc = 'LOG' THEN f.size END) * 8.0 / 1024 AS DECIMAL(18,2)) AS TotalLogSize_MB
FROM sys.databases d
JOIN sys.master_files f ON d.database_id = f.database_id
GROUP BY d.name, d.recovery_model_desc, d.log_reuse_wait_desc
ORDER BY TotalLogSize_MB DESC;

-- CÁCH DỰ PHÒNG: Nếu muốn xem % Log đã dùng chính xác trên toàn server:
-- DBCC SQLPERF(LOGSPACE); 


2. Kiểm tra chi tiết dung lượng ổ đĩa từ bên trong SQL (Kiểm tra ổ F:)

sql
SELECT DISTINCT 
    volume_mount_point AS Drive, 
    file_system_type AS FileSystem, 
    total_bytes/1024/1024/1024 AS TotalSize_GB, 
    available_bytes/1024/1024/1024 AS Available_GB,
    CAST(available_bytes * 100.0 / total_bytes AS DECIMAL(10,2)) AS FreePercentage
FROM sys.master_files AS f
CROSS APPLY sys.dm_os_volume_stats(f.database_id, f.file_id)
WHERE volume_mount_point = 'F:\'; -- Lọc riêng ổ F nếu cần


3. Kiểm tra các Session đang chạy ngầm làm treo Log
Đôi khi một Transaction dài chưa commit sẽ khiến Log không thể bị xóa (Truncate).

sql
SELECT 
    st.session_id,
    st.transaction_id,
    at.name AS TransactionName,
    at.transaction_begin_time,
    DATEDIFF(MINUTE, at.transaction_begin_time, GETDATE()) AS DurationMinutes,
    s.host_name,
    s.program_name
FROM sys.dm_tran_active_transactions at
JOIN sys.dm_tran_session_transactions st ON at.transaction_id = st.transaction_id
JOIN sys.dm_exec_sessions s ON st.session_id = s.session_id
ORDER BY at.transaction_begin_time;

-- ======================================================
-- KỊCH BẢN XỬ LÝ RIÊNG CHO DATABASE MCAFEE (Đang chiếm ~75GB Log)
-- ======================================================

-- BƯỚC 1: Lấy tên Logic của file Log (Cần tên này để chạy lệnh Shrink)
SELECT name AS LogicalName, physical_name AS PhysicalPath, type_desc
FROM sys.master_files 
WHERE database_id IN (DB_ID('mcafee'), DB_ID('mcafee_Events')) AND type_desc = 'LOG';

-- BƯỚC 2: Backup Log để giải phóng không gian (CHỌN Ổ ĐĨA CÒN TRỐNG, KHÔNG CHỌN Ổ F)
-- Giả sử backup sang ổ D hoặc E:
BACKUP LOG [mcafee] TO DISK = 'D:\Backup\mcafee_log_emergency.trn' WITH COMPRESSION, STATS = 10;
BACKUP LOG [mcafee_Events] TO DISK = 'D:\Backup\mcafee_Events_log_emergency.trn' WITH COMPRESSION, STATS = 10;

-- ======================================================
-- QUY TRÌNH SHRINK LOG AN TOÀN (Cần check kỹ trước khi thực hiện)
-- ======================================================

-- KIỂM TRA 1: Đảm bảo lý do kẹt log là 'NOTHING' hoặc 'CHECKPOINT'
-- Nếu là 'LOG_BACKUP', lệnh Shrink sẽ không có tác dụng. Cần chạy Backup Log trước.
SELECT name, log_reuse_wait_desc 
FROM sys.databases 
WHERE name IN ('mcafee', 'mcafee_Events');

-- KIỂM TRA 2: Kiểm tra tỷ lệ trống thực tế (Log Used %)
-- Chạy lệnh này và nhìn cột 'Log Space Used (%)'. 
-- Nếu con số này > 50%, lệnh Shrink sẽ KHÔNG giải phóng được nhiều dung lượng.
-- Mục tiêu: Số này phải thấp (< 10-20%) sau khi Backup Log thì Shrink mới an toàn và hiệu quả.
DBCC SQLPERF(LOGSPACE);

-- KIỂM TRA 3: Kiểm tra Transaction đang mở (Đã có ở Query 3 phía trên)
-- Đảm bảo không có giao dịch nào kéo dài hàng tiếng đồng hồ.

-- KIỂM TRA 4: Lấy LogicalName một lần nữa để chắc chắn
SELECT name AS LogicalName, size/128.0 AS CurrentSize_MB
FROM sys.master_files 
WHERE database_id = DB_ID('mcafee') AND type_desc = 'LOG';


-- THỰC HIỆN (Chỉ khi 3 kiểm tra trên đã OK):
-- Bước A: Backup Log (Bắt buộc để làm trống không gian bên trong file)
-- BACKUP LOG [mcafee] TO DISK = 'D:\Backup\mcafee_log.trn';

-- Bước B: Shrink file về kích thước mong muốn (VD: 2GB = 2048MB)
-- DBCC SHRINKFILE (N'mcafee_log', 2048);

-- ======================================================
-- LỜI KHUYÊN: CÓ NÊN DÙNG SHRINKDATABASE KHÔNG?
-- ======================================================
-- KHÔNG NÊN dùng DBCC SHRINKDATABASE ('mcafee_Events') vì:
-- 1. Nó sẽ thu nhỏ CẢ file Data (.mdf) và file Log (.ldf).
-- 2. Việc thu nhỏ file Data gây PHÂN MẢNH (Fragmentation) cực nặng, làm chậm hệ thống sau này.
-- 3. Nó tốn rất nhiều tài nguyên CPU/IO vì phải di chuyển các page dữ liệu.

-- GIẢI PHÁP TỐI ƯU: Chỉ dùng DBCC SHRINKFILE cho file Log (.ldf).
-- Cách này chỉ tác động lên file đang gây đầy ổ F, không ảnh hưởng đến dữ liệu và hiệu năng chung.

-- BƯỚC THỰC HIỆN CHUẨN:
-- ======================================================
-- CHIẾN THUẬT GỠ KẸT 'OLDEST_PAGE' (Cho Database mcafee)
-- ======================================================
-- Mô tả: OLDEST_PAGE có nghĩa là SQL Server đang đợi tiến trình ghi dữ liệu xuống đĩa (Checkpoint)
-- hoặc một tiến trình quét trang cũ hoàn tất.

-- Bước 1: Ép SQL Server ghi dữ liệu từ Ram xuống đĩa ngay lập tức
USE [mcafee];
GO
CHECKPOINT;
GO

-- Bước 2: Chạy lại lệnh Backup Log (Để đánh dấu điểm có thể tái sử dụng Log)
BACKUP LOG [mcafee] TO DISK = 'D:\Backup\mcafee_log_retry.trn' WITH COMPRESSION;
GO

-- Bước 3: Kiểm tra lại xem đã về 'NOTHING' chưa
SELECT name, log_reuse_wait_desc FROM sys.databases WHERE name = 'mcafee';

-- Bước 4: Chạy Shrink nếu đã là 'NOTHING'
-- DBCC SHRINKFILE (N'mcafee_log', 2048);


-- ======================================================
-- CHO DATABASE mcafee_Events (Đã báo NOTHING - Sẵn sàng Shrink)
-- ======================================================
-- Vì đã báo NOTHING, bạn có thể thực hiện Shrink ngay (nên backup log 1 lần cuối trước khi shrink).
-- BACKUP LOG [mcafee_Events] TO DISK = 'D:\Backup\mcafee_Events_final.trn';
-- ======================================================
-- KIỂM TRA HỆ THỐNG BACKUP ĐỊNH KỲ
-- ======================================================

-- 1. Kiểm tra xem có các Job Backup nào đang tồn tại trong SQL Agent không
SELECT 
    name AS JobName,
    enabled AS IsEnabled,
    description AS JobDescription,
    date_created,
    date_modified
FROM msdb.dbo.sysjobs
WHERE name LIKE '%Backup%' OR name LIKE '%mcafee%'
ORDER BY enabled DESC, name;

-- 2. Kiểm tra lịch sử Backup thực tế (Full, Log) trong 7 ngày gần đây
-- Giúp bạn biết lần cuối cùng database được backup là khi nào
SELECT 
    s.database_name,
    CASE s.type 
        WHEN 'D' THEN 'Full Backup'
        WHEN 'L' THEN 'Log Backup'
        WHEN 'I' THEN 'Differential Backup'
    END AS BackupType,
    s.backup_start_date,
    s.backup_finish_date,
    CAST(s.backup_size / 1024 / 1024 AS DECIMAL(10, 2)) AS Size_MB,
    m.physical_device_name AS BackupLocation
FROM msdb.dbo.backupset s
JOIN msdb.dbo.backupmediafamily m ON s.media_set_id = m.media_set_id
WHERE s.database_name IN ('mcafee', 'mcafee_Events')
  AND s.backup_start_date > DATEADD(day, -7, GETDATE())
ORDER BY s.backup_start_date DESC;

Hướng xử lý nhanh (Tùy theo cột LogReuseWaitReason ở Query 1):
Nếu là LOG_BACKUP: Database đang ở chế độ FULL Recovery nhưng chưa được backup Log. Bạn cần chạy Backup Log ngay lập tức để giải phóng không gian bên trong file Log.
Lệnh: BACKUP LOG [TenDatabase] TO DISK = 'D:\Backup\TenDatabase_Log.trn'
Nếu là ACTIVE_TRANSACTION: Có giao dịch đang treo. Bạn dùng Query 3 để tìm session_id và có thể cân nhắc KILL [session_id] nếu nó là lỗi.
-- ======================================================
-- ĐIỀU TRA NGHỊCH LÝ: CÓ JOB BACKUP MÀ Ổ VẪN ĐẦY?
-- ======================================================

-- 1. Kiểm tra lịch sử chạy Job trong 24 giờ qua (Xem có bị lỗi FAILED không)
SELECT 
    j.name AS JobName,
    h.run_date,
    h.run_time,
    CASE h.run_status 
        WHEN 0 THEN 'FAILED'
        WHEN 1 THEN 'Succeeded'
        WHEN 2 THEN 'Retry'
        WHEN 3 THEN 'Canceled'
    END AS Status,
    h.message AS ErrorMessage
FROM msdb.dbo.sysjobhistory h
JOIN msdb.dbo.sysjobs j ON h.job_id = j.job_id
WHERE j.name LIKE '%Backup%' -- Thay tên Job của bạn vào đây nếu cần
  AND h.instance_id > 0
  AND h.run_date >= CONVERT(VARCHAR(8), GETDATE(), 112)
ORDER BY h.run_date DESC, h.run_time DESC;


-- 2. TẠI SAO BACKUP MÀ Ổ VẪN ĐẦY?
-- Có 2 khả năng chính:

-- KHẢ NĂNG 1: "File to nhưng ruột trống"
-- Lệnh BACKUP LOG chỉ làm trống "nội dung" bên trong file .ldf để SQL ghi đè dữ liệu mới vào.
-- Nó KHÔNG tự động cắt bớt kích thước file vật lý trên ổ đĩa. 
-- Ví dụ: File Log đã phình lên 60GB thì nó vẫn sẽ chiếm 60GB trên ổ F mãi mãi, cho đến khi bạn chạy lệnh SHRINKFILE.

-- KHẢ NĂNG 2: "Log tăng trưởng quá nhanh"
-- Nếu trong 15 phút giữa 2 lần backup, database có một tác vụ Xử lý dữ liệu cực lớn, 
-- file Log có thể phình to hơn toàn bộ dung lượng trống còn lại của ổ đĩa trước khi kịp đến lần backup tiếp theo.


-- BƯỚC CẦN LÀM BÂY GIỜ:
-- ======================================================
-- GIẢI THÍCH: TẠI SAO BACKUP SANG G NHƯNG F VẪN ĐẦY?
-- ======================================================
-- Bạn có thể hình dung qua sơ đồ sau:

-- 1. FILE LOG VẬT LÝ (.ldf): Nằm ở ổ F:\ (Đây là cái "Thùng chứa")
-- 2. FILE BACKUP (.trn): Lưu ở ổ G:\ (Đây là "Bản sao dữ liệu")

-- CƠ CHẾ HOẠT ĐỘNG:
-- Khi Job chạy: Nó copy nội dung từ Thùng (F:) vào Bản sao (G:).
-- Sau khi copy xong: SQL Server báo "Tôi đã dọn dẹp nội dung trong Thùng (F:) rồi, bạn có thể đổ rác mới vào".
-- NHƯNG: Cái Thùng (File .ldf) nó KHÔNG tự co lại. Nó vẫn chiếm đúng 60GB-70GB trên ổ F:\.

-- ĐỂ GIẢI QUYẾT: 
-- Bạn phải dùng lệnh SHRINKFILE để SQL Server "cắt bớt" vỏ cái Thùng (F:) đi. 
-- Khi đó ổ F:\ mới hiện ra dung lượng trống.

-- ======================================================
-- QUERY TRA CỨU TÊN LOGIC VÀ VỊ TRÍ VẬT LÝ CHI TIẾT
-- ======================================================
-- Sử dụng query này để biết chính xác file nào đang nằm ở ổ F và tên Logic là gì để Shrink.

SELECT 
    d.name AS DatabaseName,
    f.name AS LogicalName,       -- Dùng tên này cho lệnh DBCC SHRINKFILE
    f.physical_name AS PhysicalPath, -- Đường dẫn thực tế trên ổ đĩa
    f.type_desc AS FileType,    -- DATA (Dữ liệu) hoặc LOG (Nhật ký)
    CAST(f.size * 8.0 / 1024 AS DECIMAL(18,2)) AS Size_MB
FROM sys.master_files f
JOIN sys.databases d ON f.database_id = d.database_id
WHERE d.name IN ('mcafee', 'mcafee_Events') -- Có thể bỏ dòng này để xem toàn bộ server
ORDER BY d.name, f.type;
Nếu Log đã trống (FreeLogSize_MB lớn) nhưng file vật lý vẫn to: Bạn có thể Shrink file Log để lấy lại dung lượng cho ổ đĩa F.
Lệnh: DBCC SHRINKFILE (N'TenLogicalName_Log', 1024); (1024 là dung lượng đích MB).