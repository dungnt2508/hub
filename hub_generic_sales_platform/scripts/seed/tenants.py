import uuid
from sqlalchemy import select
from app.infrastructure.database.models import Tenant, UserAccount, TenantStatus, TenantPlan, UserRole, UserStatus
from app.core.services.auth_service import AuthService

async def seed_tenants(db):
    print("Seeding Tenants & Users...")
    tenants_data = [
        {"name": "Sunrise Property", "email_prefix": "sunrise"},
        {"name": "IvyPrep Education", "email_prefix": "ivy"},
        {"name": "F888 Finance", "email_prefix": "f888"},
        {"name": "AnyCar Auto", "email_prefix": "anycar"},
    ]
    
    tenant_ids = {}

    for t_data in tenants_data:
        tenant_name = t_data["name"]
        res = await db.execute(select(Tenant).where(Tenant.name == tenant_name))
        tenant = res.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name=tenant_name,
                status=TenantStatus.ACTIVE,
                plan=TenantPlan.PRO
            )
            db.add(tenant)
            await db.flush()
            print(f"Created Tenant: {tenant_name}")
        
        tenant_ids[t_data["email_prefix"]] = str(tenant.id)

        # Create Owner for each
        email = f"owner@{t_data['email_prefix']}.vn"
        res = await db.execute(select(UserAccount).where(UserAccount.email == email))
        if not res.scalar_one_or_none():
            password_hash = AuthService.hash_password("123456")
            user = UserAccount(
                tenant_id=str(tenant.id),
                email=email,
                role=UserRole.OWNER,
                status=UserStatus.ACTIVE,
                password_hash=password_hash
            )
            db.add(user)
            print(f"  -> Created Owner: {email}")

    return tenant_ids
    # (Old user loop removed)

