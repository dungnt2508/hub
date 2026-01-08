# Admin Audit Logs Implementation

**Status**: ✅ **COMPLETE**  
**Date**: 2025-01-XX

---

## ✅ Đã Hoàn Thành

### 1. Audit Log Service ✅
**File**: `backend/domain/admin/audit_log_service.py`

**Features:**
- ✅ Log mọi thay đổi config (create, update, delete, enable, disable, rollback)
- ✅ Tính toán diff tự động giữa old và new values
- ✅ Serialize values (UUID, datetime, dict, etc.) thành JSON
- ✅ Support filtering và pagination
- ✅ Error handling - audit logging failure không làm break operation

**Methods:**
- `log_config_change()` - Log một config change
- `list_audit_logs()` - List audit logs với filters

### 2. Tích Hợp vào Admin Config Service ✅

**File**: `backend/domain/admin/admin_config_service.py`

**Audit Logging được tích hợp vào:**
- ✅ Pattern Rules: create, update, delete, enable, disable
- ✅ Keyword Hints: create, update, delete
- ✅ Routing Rules: create, update, delete
- ✅ Prompt Templates: create, update, delete, rollback
- ✅ Tool Permissions: create, update, delete
- ✅ Guardrails: create, update, delete

**Mỗi operation tự động log:**
- Config type, ID, name
- Action (create/update/delete/enable/disable/rollback)
- Changed by (user ID)
- Old value (snapshot trước khi thay đổi)
- New value (snapshot sau khi thay đổi)
- Diff (chỉ các fields thay đổi)
- Tenant ID
- Timestamp

### 3. Audit Logs API ✅

**File**: `backend/interface/admin_api.py`

**Endpoint:**
- ✅ `GET /api/admin/v1/audit-logs`

**Query Parameters:**
- `tenant_id` (optional): Filter by tenant
- `config_type` (optional): Filter by config type (pattern_rule, keyword_hint, etc.)
- `config_id` (optional): Filter by specific config ID
- `changed_by` (optional): Filter by user ID
- `start_date` (optional): ISO format datetime
- `end_date` (optional): ISO format datetime
- `limit` (default: 100, max: 500): Page size
- `offset` (default: 0): Page offset

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid|null",
      "config_type": "pattern_rule",
      "config_id": "uuid",
      "config_name": "HR Leave Query",
      "changed_by": "uuid",
      "changed_by_email": "admin@example.com",
      "action": "create",
      "old_value": null,
      "new_value": {...},
      "diff": null,
      "changed_at": "2025-01-01T00:00:00Z",
      "reason": null
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

### 4. Database Schema ✅

**Table**: `config_audit_logs`

**Columns:**
- `id` (UUID, primary key)
- `tenant_id` (UUID, foreign key)
- `config_type` (VARCHAR) - pattern_rule, keyword_hint, routing_rule, etc.
- `config_id` (UUID)
- `config_name` (VARCHAR)
- `changed_by` (UUID) - admin user ID
- `changed_by_email` (VARCHAR)
- `action` (VARCHAR) - create, update, delete, enable, disable, rollback
- `old_value` (JSONB) - snapshot trước khi thay đổi
- `new_value` (JSONB) - snapshot sau khi thay đổi
- `diff` (JSONB) - chỉ các fields thay đổi
- `changed_at` (TIMESTAMP)
- `reason` (TEXT) - optional reason

**Indexes:**
- `idx_config_audit_logs_tenant` - (tenant_id, changed_at)
- `idx_config_audit_logs_config` - (config_type, config_id, changed_at)
- `idx_config_audit_logs_user` - (changed_by, changed_at)

---

## Usage Examples

### 1. Xem tất cả audit logs
```bash
GET /api/admin/v1/audit-logs?limit=50
```

### 2. Xem audit logs cho một config cụ thể
```bash
GET /api/admin/v1/audit-logs?config_type=pattern_rule&config_id=<uuid>
```

### 3. Xem audit logs của một user
```bash
GET /api/admin/v1/audit-logs?changed_by=<user_uuid>
```

### 4. Xem audit logs trong khoảng thời gian
```bash
GET /api/admin/v1/audit-logs?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z
```

---

## Implementation Details

### Diff Calculation

Audit log service tự động tính toán diff giữa old và new values:
- Chỉ log các fields thay đổi
- Format: `{"field_name": {"old": "...", "new": "..."}}`
- Handle JSON fields (parse nếu là string)
- Skip nếu values giống nhau

### Serialization

Service tự động serialize các types:
- UUID → string
- datetime → ISO format string
- dict/list → JSON
- Pydantic models → dict via `.dict()`

### Error Handling

Audit logging được thiết kế để không làm break operation:
- Nếu audit log fail, chỉ log warning
- Operation vẫn tiếp tục bình thường
- Không raise exception

---

## Next Steps

### Future Enhancements
1. **RBAC Integration**: Lấy email từ admin_users table
2. **Export**: Export audit logs to CSV/JSON
3. **Retention Policy**: Auto-delete old logs sau X ngày
4. **Real-time Notifications**: WebSocket cho real-time audit log updates
5. **Advanced Filtering**: Full-text search, regex patterns

---

**Status**: ✅ Complete  
**Next**: RBAC Authentication Implementation

