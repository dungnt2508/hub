"""
Script to create default admin user on startup
Usage: python -m backend.scripts.create_default_admin
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.domain.admin.admin_user_service import AdminUserService
from backend.infrastructure.database_client import database_client
from backend.shared.logger import logger
from backend.shared.exceptions import NotFoundError


async def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        # Initialize database connection
        await database_client.connect()
        
        # Get admin user credentials from environment variables
        admin_email = os.getenv("ADMIN_EMAIL", "gsnake1102@gmail.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "gsnake6789")
        admin_role = os.getenv("ADMIN_ROLE", "admin")
        
        service = AdminUserService()
        
        # Check if admin user already exists
        try:
            existing_user = await service.get_admin_user_by_email(admin_email)
            logger.info(f"Admin user {admin_email} already exists, skipping creation")
            print(f"ℹ️  Admin user {admin_email} already exists, skipping creation")
            return
        except NotFoundError:
            # User doesn't exist, create it
            pass
        
        # Create admin user
        logger.info(f"Creating default admin user: {admin_email}")
        user = await service.create_admin_user(
            email=admin_email,
            password=admin_password,
            role=admin_role,
            tenant_id=None,  # Global admin
        )
        
        logger.info(f"✅ Successfully created admin user: {user['email']} (role: {user['role']})")
        print(f"✅ Default admin user created: {admin_email} / {admin_password}")
        
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}", exc_info=True)
        print(f"❌ Failed to create default admin user: {e}")
        # Don't exit with error, just log it
        # This allows the container to start even if admin creation fails
    finally:
        # Close database connection
        try:
            await database_client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(create_default_admin())

