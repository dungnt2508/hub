"""
Admin User Service - CRUD operations for admin users
"""
import bcrypt
import json
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from ...shared.logger import logger
from ...shared.exceptions import NotFoundError, ValidationError, AuthenticationError
from ...infrastructure.database_client import database_client


class AdminUserService:
    """Service for admin user CRUD operations"""
    
    def __init__(self):
        self.db = database_client
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    async def create_admin_user(
        self,
        email: str,
        password: str,
        role: str,  # 'admin' | 'operator' | 'viewer'
        tenant_id: Optional[UUID] = None,
        permissions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create admin user"""
        pool = self.db.pool
        
        # Validate role
        valid_roles = ['admin', 'operator', 'viewer']
        if role not in valid_roles:
            raise ValidationError(f"Invalid role. Must be one of: {valid_roles}")
        
        # Validate email format (basic)
        if '@' not in email or '.' not in email.split('@')[1]:
            raise ValidationError("Invalid email format")
        
        # Validate password strength
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        # Check if email already exists
        async with pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM admin_users WHERE email = $1",
                email.lower()
            )
        
        if existing:
            raise ValidationError(f"User with email {email} already exists")
        
        # Hash password
        password_hash = self._hash_password(password)
        
        user_id = uuid4()
        now = datetime.utcnow()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO admin_users (
                    id, email, password_hash, role, permissions,
                    tenant_id, active, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, true, $7, $8
                ) RETURNING *
                """,
                user_id,
                email.lower(),
                password_hash,
                role,
                json.dumps(permissions or {}),
                tenant_id,
                now,
                now,
            )
        
        return self._user_from_row(row)
    
    async def get_admin_user(self, user_id: UUID) -> Dict[str, Any]:
        """Get admin user by ID"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM admin_users WHERE id = $1",
                user_id
            )
        
        if not row:
            raise NotFoundError(f"Admin user {user_id} not found")
        
        return self._user_from_row(row)
    
    async def get_admin_user_by_email(self, email: str) -> Dict[str, Any]:
        """Get admin user by email"""
        pool = self.db.pool
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM admin_users WHERE email = $1",
                email.lower()
            )
        
        if not row:
            raise NotFoundError(f"Admin user with email {email} not found")
        
        return self._user_from_row(row)
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            user = await self.get_admin_user_by_email(email)
        except NotFoundError:
            # Don't reveal if user exists
            raise AuthenticationError("Invalid email or password")
        
        # Check if user is active
        if not user.get("active"):
            raise AuthenticationError("User account is inactive")
        
        # Verify password
        if not self._verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid email or password")
        
        # Update last_login_at
        pool = self.db.pool
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE admin_users SET last_login_at = $1 WHERE id = $2",
                datetime.utcnow(),
                user["id"]
            )
        
        # Remove password_hash from response
        user.pop("password_hash", None)
        
        return user
    
    async def list_admin_users(
        self,
        tenant_id: Optional[UUID] = None,
        role: Optional[str] = None,
        active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List admin users"""
        pool = self.db.pool
        
        query = "SELECT * FROM admin_users WHERE 1=1"
        params = []
        param_idx = 1
        
        if tenant_id:
            query += f" AND (tenant_id = ${param_idx} OR tenant_id IS NULL)"
            params.append(tenant_id)
            param_idx += 1
        
        if role:
            query += f" AND role = ${param_idx}"
            params.append(role)
            param_idx += 1
        
        if active is not None:
            query += f" AND active = ${param_idx}"
            params.append(active)
            param_idx += 1
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_query, *params)
        
        # Get items
        query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        items = [self._user_from_row(row) for row in rows]
        
        # Remove password_hash from all items
        for item in items:
            item.pop("password_hash", None)
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    async def update_admin_user(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update admin user"""
        existing = await self.get_admin_user(user_id)
        
        pool = self.db.pool
        updates = []
        params = []
        param_idx = 1
        
        if email is not None:
            # Validate email
            if '@' not in email or '.' not in email.split('@')[1]:
                raise ValidationError("Invalid email format")
            
            # Check if email already exists (for other user)
            async with pool.acquire() as conn:
                other_user = await conn.fetchrow(
                    "SELECT id FROM admin_users WHERE email = $1 AND id != $2",
                    email.lower(),
                    user_id
                )
            
            if other_user:
                raise ValidationError(f"Email {email} already in use")
            
            updates.append(f"email = ${param_idx}")
            params.append(email.lower())
            param_idx += 1
        
        if password is not None:
            # Validate password
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters")
            
            password_hash = self._hash_password(password)
            updates.append(f"password_hash = ${param_idx}")
            params.append(password_hash)
            param_idx += 1
        
        if role is not None:
            valid_roles = ['admin', 'operator', 'viewer']
            if role not in valid_roles:
                raise ValidationError(f"Invalid role. Must be one of: {valid_roles}")
            
            updates.append(f"role = ${param_idx}")
            params.append(role)
            param_idx += 1
        
        if permissions is not None:
            import json
            updates.append(f"permissions = ${param_idx}")
            params.append(json.dumps(permissions))
            param_idx += 1
        
        if active is not None:
            updates.append(f"active = ${param_idx}")
            params.append(active)
            param_idx += 1
        
        if not updates:
            return existing
        
        updates.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())
        param_idx += 1
        
        params.append(user_id)
        
        query = f"""
            UPDATE admin_users
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING *
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        
        if not row:
            raise NotFoundError(f"Admin user {user_id} not found")
        
        result = self._user_from_row(row)
        result.pop("password_hash", None)
        return result
    
    async def delete_admin_user(self, user_id: UUID):
        """Delete admin user"""
        existing = await self.get_admin_user(user_id)
        
        pool = self.db.pool
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM admin_users WHERE id = $1",
                user_id
            )
    
    def _user_from_row(self, row) -> Dict[str, Any]:
        """Convert database row to user dict"""
        import json
        
        return {
            "id": row["id"],
            "email": row["email"],
            "password_hash": row.get("password_hash"),  # Will be removed in responses
            "role": row["role"],
            "permissions": json.loads(row["permissions"]) if row.get("permissions") else {},
            "tenant_id": row["tenant_id"],
            "active": row["active"],
            "last_login_at": row["last_login_at"].isoformat() if row.get("last_login_at") else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }


# Global service instance
admin_user_service = AdminUserService()

