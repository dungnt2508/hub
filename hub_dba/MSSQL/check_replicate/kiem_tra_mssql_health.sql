/*
===============================================================================
KỊCH BẢN KIỂM TRA TRẠNG THÁI MIRRORING VÀ BACKUP JOB
Hệ thống: Primary (10.90) - Mirror (10.91)
===============================================================================
*/

-- 1. KIỂM TRA TRẠNG THÁI MIRRORING CỦA CÁC DATABASE
-- Trạng thái mong muốn: mirroring_state_desc = 'SYNCHRONIZED'
SELECT 
    db_name(database_id) AS [Tên Database],
    mirroring_state_desc AS [Trạng Thái Mirror],
    mirroring_role_desc AS [Vai Trò (Role)],
    mirroring_safety_level_desc AS [Mức Độ An Toàn],
    mirroring_partner_name AS [Máy Chủ Đối Tác],
    mirroring_partner_instance AS [Instance Đối Tác]
FROM sys.database_mirroring
WHERE mirroring_guid IS NOT NULL;

-- 2. KIỂM TRA CÁC JOB BACKUP VÀ ĐƯỜNG DẪN DISK
-- LƯU Ý: Trên máy Mirror (10.91), thông thường sẽ KHÔNG có Job nếu chưa được copy sang.
-- Nếu máy này là Mirror, các DB sẽ ở trạng thái 'Restoring', không thể backup được.
SELECT 
    j.name AS [Tên Job],
    j.enabled AS [Đang Bật],
    s.step_id AS [Bước],
    s.step_name AS [Tên Bước],
    s.command AS [Lệnh/Đường Dẫn Backup],
    CASE 
        WHEN EXISTS (SELECT 1 FROM sys.database_mirroring WHERE mirroring_role_desc = 'PRINCIPAL') THEN 'Sẵn sàng Backup (Là máy Chính)'
        ELSE 'Máy Mirror - Không thể backup lúc này'
    END AS [Khả năng Backup]
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps s ON j.job_id = s.job_id
WHERE j.name LIKE '%Backup%' 
ORDER BY j.name, s.step_id;

-- Mẹo: Để backup chạy được trên cả 2 máy khi failover, lệnh backup nên có kiểm tra role:
/*
IF (SELECT mirroring_role_desc FROM sys.database_mirroring WHERE database_id = DB_ID('Ten_DB')) = 'PRINCIPAL'
BEGIN
    BACKUP DATABASE [Ten_DB] TO DISK = 'S:\Backup\Ten_DB.bak' ...
END
*/

-- 3. KIỂM TRA LỊCH SỬ BACKUP GẦN NHẤT
-- Để xác định xem backup có đang chạy thành công vào Disk mới hay không
SELECT TOP 20
    database_name AS [Tên DB],
    backup_start_date AS [Thời Gian Bắt Đầu],
    backup_finish_date AS [Thời Gian Kết Thúc],
    physical_device_name AS [Đường Dẫn Vật Lý],
    CASE type 
        WHEN 'D' THEN 'Full'
        WHEN 'I' THEN 'Differential'
        WHEN 'L' THEN 'Log'
    END AS [Loại Backup]
FROM msdb.dbo.backupset bs
JOIN msdb.dbo.backupmediafamily bmf ON bs.media_set_id = bmf.media_set_id
ORDER BY backup_finish_date DESC;
