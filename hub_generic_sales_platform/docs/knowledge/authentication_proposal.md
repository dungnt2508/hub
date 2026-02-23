# Đề xuất Authentication & Authorization System

## Phân tích hiện trạng

### Vấn đề hiện tại
1. **TenantMiddleware đang validate tenant_id trực tiếp từ header**
   - Không có authentication
   - Client có thể gửi bất kỳ tenant_id nào
   - Không có cách xác định user đang login

2. **Thiếu authentication flow**
   - Không có login endpoint
   - Không có JWT/session management
   - UserAccount model không có password field

3. **Security gap**
   - Admin dashboard cần authentication
   - User phải login trước khi access
   - Cần phân quyền dựa trên role (owner, admin, viewer)

## Phương án đề xuất

### Option 1: JWT-based Authentication (Khuyến nghị)

**Flow:**
```
1. User login → POST /api/auth/login
   - Input: email, password
   - Validate user_account (email, password, status=active)
   - Generate JWT token chứa: { user_id, tenant_id, role, email }
   - Return: { access_token, user: { id, email, role, tenant_id } }

2. Client gửi request với header: Authorization: Bearer <token>

3. AuthMiddleware:
   - Extract JWT từ Authorization header
   - Validate JWT signature & expiry
   - Decode để lấy user_id, tenant_id
   - Query user_account để verify user còn active
   - Set vào request.state: user_id, tenant_id, user_role
   - Validate tenant status = active

4. Endpoints tự động có:
   - request.state.user_id
   - request.state.tenant_id  
   - request.state.user_role
```

**Ưu điểm:**
- Stateless (không cần session storage)
- Scalable
- Standard (JWT)
- Dễ implement

**Nhược điểm:**
- Cần thêm password field vào UserAccount
- Cần password hashing (bcrypt)

### Option 2: Session-based Authentication

**Flow:**
```
1. User login → POST /api/auth/login
   - Create session trong database/redis
   - Return session_id

2. Client gửi session_id trong cookie hoặc header

3. AuthMiddleware:
   - Validate session_id
   - Load user từ session
   - Set vào request.state
```

**Ưu điểm:**
- Có thể revoke session dễ dàng
- Phù hợp với multi-device

**Nhược điểm:**
- Cần session storage (Redis/DB)
- Stateful

### Option 3: API Key cho Admin Dashboard (Đơn giản nhất)

**Flow:**
```
1. Admin có API key được generate từ backend
2. Client gửi: X-API-Key: <key>
3. AuthMiddleware:
   - Validate API key
   - Map key → user_account → tenant_id
```

**Ưu điểm:**
- Đơn giản, nhanh implement
- Phù hợp cho internal admin tool

**Nhược điểm:**
- Kém bảo mật hơn JWT
- Khó revoke

## Recommendation: Option 1 (JWT)

### Implementation Plan

#### Phase 1: Database Schema Update
```python
# Thêm password field vào UserAccount
class UserAccount(Base):
    # ... existing fields
    password_hash = Column(String, nullable=True)  # Nullable để support existing users
```

#### Phase 2: Authentication Service
```python
# app/core/services/auth_service.py
class AuthService:
    async def authenticate(email: str, password: str) -> Optional[UserAccount]:
        # Validate email & password
        # Return user if valid
        
    def generate_jwt(user: UserAccount) -> str:
        # Create JWT with user_id, tenant_id, role, email
        
    def verify_jwt(token: str) -> Dict:
        # Verify & decode JWT
```

#### Phase 3: Auth Middleware
```python
# app/interfaces/middleware/auth.py
class AuthMiddleware:
    async def dispatch(self, request, call_next):
        # Extract JWT from Authorization header
        # Verify JWT
        # Load user_account
        # Set request.state.user_id, tenant_id, role
        # Validate tenant active
```

#### Phase 4: API Endpoints
```python
# app/interfaces/api/auth.py
@api_router.post("/auth/login")
async def login(credentials: LoginRequest):
    # Authenticate
    # Generate JWT
    # Return token

@api_router.post("/auth/logout")  # Optional
async def logout():
    # Invalidate token (nếu dùng blacklist)
```

#### Phase 5: Update Existing Endpoints
- Remove `x_tenant_id: str = Header(...)` 
- Use `request.state.tenant_id` instead
- Add role-based authorization nếu cần

### Migration Strategy

1. **Backward compatibility:**
   - Giữ TenantMiddleware nhưng make it optional
   - Nếu có JWT → dùng AuthMiddleware
   - Nếu không có JWT → fallback to X-Tenant-ID (deprecated)

2. **Gradual rollout:**
   - Phase 1: Add auth endpoints (không bắt buộc)
   - Phase 2: Update frontend để dùng JWT
   - Phase 3: Deprecate X-Tenant-ID header
   - Phase 4: Remove TenantMiddleware

## Code Structure

```
app/
├── core/
│   ├── services/
│   │   └── auth_service.py      # JWT generation, password hashing
│   └── entities/
│       └── tenant.py            # Add password_hash field
├── interfaces/
│   ├── middleware/
│   │   ├── auth.py               # NEW: AuthMiddleware
│   │   └── tenant.py             # DEPRECATED: Keep for backward compat
│   └── api/
│       └── auth.py               # NEW: Login/logout endpoints
└── infrastructure/
    └── database/
        └── tenant.py             # UserAccountRepository: add password methods
```

## Security Considerations

1. **Password hashing:** Use bcrypt với salt rounds >= 12
2. **JWT expiry:** Access token 1 hour, Refresh token 7 days
3. **HTTPS only:** JWT chỉ gửi qua HTTPS
4. **Rate limiting:** Login endpoint cần rate limit
5. **Password policy:** Min 8 chars, complexity requirements

## Next Steps

1. ✅ Review & approve proposal
2. Add password_hash field to UserAccount
3. Implement AuthService
4. Implement AuthMiddleware  
5. Create login/logout endpoints
6. Update frontend to use JWT
7. Test & deploy
