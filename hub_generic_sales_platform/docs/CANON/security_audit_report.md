# Báo cáo Kiểm tra Bảo mật: Tenant Isolation & JWT Auth

**Ngày kiểm tra:** 2026-02-18  
**Phạm vi:** `app/infrastructure/database/repositories/`, `app/interfaces/api/`, Auth Middleware, `authentication_proposal.md`

---

## 1. Kiểm tra Row-level Security (tenant_id trong truy vấn SQL/SQLAlchemy)

### 1.1 Repositories ĐÁP ỨNG ĐÚNG (có tenant_id filter)

| Repository | Method | Ghi chú |
|------------|--------|---------|
| OfferingRepository | get, get_by_code, get_active_offerings, semantic_search | ✅ |
| OfferingVersionRepository | get, get_active_version, get_latest_version, semantic_search | ✅ Join với Offering, filter tenant_id |
| OfferingAttributeRepository | get, get_by_version | ✅ Join qua Version → Offering |
| OfferingVariantRepository | get, get_by_sku | ✅ |
| BotRepository | get, get_multi, get_by_code, get_active_bots, get_active_bot_by_offering | ✅ |
| BotVersionRepository | get_active_version, get_by_bot | ✅ Optional tenant_id, có filter khi có |
| TenantSalesChannelRepository | get, get_by_code | ✅ |
| TenantPriceListRepository | get, get_prices_for_offering | ✅ |
| VariantPriceRepository | get | ✅ BaseRepository |
| GuardrailRepository | get, get_active_for_tenant | ✅ |
| UseCaseRepository | get, get_by_offering, get_active | ✅ |
| FAQRepository | Tất cả methods | ✅ |
| ComparisonRepository | get, get_active, get_by_offerings | ✅ |
| InventoryRepository | get, get_stock_status, get_all_stock_status | ✅ |
| InventoryLocationRepository | get, get_by_code | ✅ |
| SessionRepository | get (BaseRepository), get_active_sessions, list_for_logs | ✅ |
| ConversationTurnRepository | get_by_session | ✅ Join Session, filter tenant_id |
| ContextSlotRepository | get_by_session | ✅ Join Session, filter tenant_id |
| DecisionRepository | get, get_by_session | ✅ |
| CacheRepository | get_by_message | ✅ |
| UserAccountRepository | get, get_by_email, get_by_tenant | ✅ |
| MigrationJobRepository | get, get_multi (BaseRepository) | ✅ MigrationJob có tenant_id |

### 1.2 Repositories CÓ LỖ HỔNG Tenant Leakage

#### ~~🔴 NGHIÊM TRỌNG~~ ✅ ĐÃ SỬA: SessionRepository.get_by_bot_and_channel

**File:** `app/infrastructure/database/repositories/session_repo.py`

**Đã sửa:** Thêm `SessionModel.tenant_id == tenant_id` vào WHERE clause.

---

#### ~~🟠 TRUNG BÌNH~~ ✅ ĐÃ SỬA: ContextSlotRepository.get_by_key

**File:** `app/infrastructure/database/repositories/session_repo.py`

**Đã sửa:** Thêm tham số `tenant_id`, join với `SessionModel` và filter `SessionModel.tenant_id == tenant_id`.

---

#### ~~🟠 TRUNG BÌNH~~ ✅ ĐÃ SỬA: ContextSlotRepository.deactivate_by_keys

**File:** `app/infrastructure/database/repositories/session_repo.py`

**Đã sửa:** Thêm tham số `tenant_id`, dùng subquery kiểm tra session thuộc tenant trước khi update.

---

#### 🟡 NHẸ: TenantAttributeConfigRepository.get

**File:** `app/infrastructure/database/repositories/ontology_repo.py` (dòng 48-54)

```python
async def get(self, id: str, tenant_id: Optional[str] = None) -> Optional[domain.TenantAttributeConfig]:
    stmt = select(AttributeConfigModel).where(AttributeConfigModel.id == id)
    if tenant_id:  # Chỉ filter KHI CÓ tenant_id
        stmt = stmt.where(AttributeConfigModel.tenant_id == tenant_id)
```

**Rủi ro:** Nếu gọi `get(id, tenant_id=None)`, sẽ trả về config của bất kỳ tenant nào. Cần kiểm tra tất cả call sites có truyền tenant_id hay không. Nếu `TenantAttributeConfig` có `tenant_id`, nên **bắt buộc** tenant_id (giống BaseRepository).

---

#### 🟡 NHẸ: BotVersionRepository.get_by_bot_and_version

**File:** `app/infrastructure/database/repositories/bot_repo.py` (dòng 98-104)

```python
async def get_by_bot_and_version(self, bot_id: str, version: int) -> Optional[domain.BotVersion]:
    stmt = select(BotVersionModel).where(
        BotVersionModel.bot_id == bot_id,
        BotVersionModel.version == version
    )
    # KHÔNG có tenant_id
```

**Rủi ro:** Bot_id thường unique toàn hệ thống nên rủi ro thấp, nhưng kiến trúc multi-tenant yêu cầu mọi truy vấn có filter tenant. Nên join Bot và filter Bot.tenant_id.

---

#### 🟡 NHẸ: ChannelConfigurationRepository

**File:** `app/infrastructure/database/repositories/bot_repo.py` (dòng 168-189)

- `get_by_bot_version_and_channel`: Không filter tenant_id
- `get_by_bot_version`: Không filter tenant_id

BotVersion liên kết với Bot có tenant_id. Nên join Bot và filter tenant khi cần kiểm chứng ownership.

---

#### 🟡 NHẸ: SemanticCacheRepository.track_hit

**File:** `app/infrastructure/database/repositories/cache_repo.py` (dòng 72-77)

```python
async def track_hit(self, cache_id: str):
    stmt = update(CacheModel).where(CacheModel.id == cache_id).values(...)
    # Không kiểm tra cache thuộc tenant nào
```

**Rủi ro:** Có thể tăng hit_count cho cache của tenant khác nếu cache_id bị biết. Rủi ro thấp nhưng nên thêm tenant_id để tuân thủ RLS.

---

### 1.3 Các model GLOBAL (không có tenant_id) – chấp nhận được

| Model | Lý do |
|-------|-------|
| DomainAttributeDefinition | GLOBAL – định nghĩa ontology dùng chung |
| KnowledgeDomain | GLOBAL – domain definition dùng chung |
| SystemCapability | GLOBAL – capability mã hóa cứng |

---

## 2. Middleware – Trích xuất tenant_id từ JWT

### 2.1 AuthMiddleware (app/interfaces/middleware/auth.py)

**Đánh giá:** ✅ Hoạt động đúng

- Lấy JWT từ header `Authorization: Bearer <token>`
- Gọi `AuthService.get_user_from_token()` để verify
- Gán `request.state.tenant_id = user.tenant_id` (dòng 130)
- Gán `request.state.user_id`, `request.state.user_role`, `request.state.user_email`
- Skip cho public paths: `/health`, `/docs`, `/api/v1/auth/login`, `/api/v1/tenants`, `/api/v1/chat/widget-message`, webhooks

**Lưu ý:** `/api/v1/tenants` là public – xem mục 4.1.

---

### 2.2 Dependencies.get_current_tenant_id (app/interfaces/api/dependencies.py)

**Đánh giá:** ~~⚠️ CÓ LỖ HỔNG~~ ✅ ĐÃ SỬA

**Đã sửa:** Bỏ fallback `X-Tenant-ID`. Chỉ dùng `request.state.tenant_id` từ JWT. Nếu thiếu → 403 với message "Valid JWT required".

---

## 3. So sánh với authentication_proposal.md – Lỗ hổng JWT Auth và RBAC

### 3.1 JWT Auth

| Yêu cầu proposal | Hiện trạng | Đánh giá |
|------------------|------------|----------|
| JWT chứa user_id, tenant_id, role, email | ✅ Có trong payload | OK |
| AuthMiddleware extract & validate JWT | ✅ Có | OK |
| Set request.state: user_id, tenant_id, user_role | ✅ Có | OK |
| Verify user_account còn active | ✅ Có | OK |
| Verify tenant status = active | ✅ Có | OK |
| Password hashing bcrypt | ✅ CryptContext, bcrypt | OK |
| JWT expiry | ✅ exp trong payload | OK |
| **Rate limiting login** | ❌ Chưa có | Lỗ hổng |
| **HTTPS only** | ⚠️ Phụ thuộc deploy | Cần cấu hình |
| **Bỏ X-Tenant-ID fallback** | ❌ Vẫn còn | Lỗ hổng (đã nêu) |

### 3.2 Legacy user không password

**File:** `app/core/services/auth_service.py` (dòng 129-134)

```python
else:
    # Legacy users without password - for backward compatibility
    logger.warning(f"User {email} has no password_hash - legacy user")
    pass  # ⚠️ Cho phép đăng nhập KHÔNG CẦN password!
```

**Rủi ro:** User cũ không có password vẫn login được với bất kỳ mật khẩu nào. Proposal ghi “In production, should require password reset”.

**Khuyến nghị:** Trong môi trường production, chặn login nếu `password_hash is None` và bắt buộc reset mật khẩu.

---

### 3.3 RBAC (Owner / Admin / Viewer)

**Hiện trạng:** ❌ **Không có triển khai RBAC**

- `user_role` được set trong `request.state` (owner/admin/viewer)
- Không có dependency hoặc decorator kiểm tra role theo endpoint
- Tất cả endpoint được bảo vệ bởi JWT nhưng không phân quyền theo role

**Proposal:** “Add role-based authorization nếu cần” – chưa được thực hiện.

**Khuyến nghị:**
- Tạo dependency `require_role(["owner", "admin"])` hoặc `require_role(["owner", "admin", "viewer"])`
- Áp dụng cho endpoint nhạy cảm (create/update/delete tenant, bot, offerings, v.v.)
- Viewer chỉ được GET, Admin/Owner được full CRUD

---

## 4. Cảnh báo Tenant Leakage

### 4.1 Admin API – ~~Thiếu authentication~~ ✅ ĐÃ SỬA

**File:** `app/interfaces/api/admin.py`

**Đã sửa:**
- Xóa `/api/v1/tenants` khỏi `public_paths` trong AuthMiddleware
- Tất cả admin endpoints yêu cầu `Depends(get_current_tenant_id)` (JWT bắt buộc)
- `list_tenants` chỉ trả về tenant mà user thuộc về
- `update/delete/patch` có `_verify_tenant_access()` – user chỉ quản lý được tenant của mình

---

### 4.2 Widget Chat – tenant_id từ request body

**File:** `app/interfaces/api/chat.py` (dòng 58-78)

```python
@chat_router.post("/chat/widget-message")  # Public endpoint
async def widget_chat_message(request: WidgetChatRequest, ...):
    result = await orchestrator.handle_message(
        tenant_id=request.tenant_id,  # ⚠️ Lấy từ BODY, client gửi gì cũng được!
        bot_id=request.bot_id,
        ...
    )
```

**Rủi ro:** Client có thể gửi `tenant_id` của tenant khác. Cần kiểm tra: bot_id có thuộc tenant_id đó không (ví dụ query Bot.where(tenant_id, bot_id)) trước khi xử lý.

---

### 4.3 Fallback X-Tenant-ID (đã nêu ở mục 2.2)

Đây là vector chính cho Tenant Leakage khi dùng JWT. Bỏ fallback là ưu tiên cao.

---

## 5. Tóm tắt Khuyến nghị

| Ưu tiên | Hạng mục | Hành động |
|---------|----------|-----------|
| P0 | Admin API | Yêu cầu JWT + role Owner/Admin cho toàn bộ tenant CRUD |
| P0 | dependencies.py | Bỏ fallback X-Tenant-ID |
| P0 | SessionRepository.get_by_bot_and_channel | Thêm `SessionModel.tenant_id == tenant_id` vào WHERE |
| P1 | RBAC | Implement `require_role` và áp dụng cho endpoint nhạy cảm |
| P1 | Widget Chat | Validate bot thuộc tenant_id trước khi xử lý |
| P1 | ContextSlotRepository.get_by_key, deactivate_by_keys | Thêm tenant_id và join Session |
| P2 | AuthService legacy user | Chặn login khi không có password_hash (prod) |
| P2 | Rate limiting | Thêm cho POST /auth/login |
| P3 | TenantAttributeConfigRepository.get | Bắt buộc tenant_id nếu model có tenant_id |
| P3 | BotVersionRepository.get_by_bot_and_version | Join Bot, filter tenant_id |
| P3 | SemanticCacheRepository.track_hit | Thêm tenant_id vào điều kiện update |

---

*Báo cáo được tạo tự động từ kiểm tra mã nguồn.*
