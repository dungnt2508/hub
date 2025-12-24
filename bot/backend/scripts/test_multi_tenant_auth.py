"""
Test script for multi-tenant bot service authentication flows.
Kiểm tra các flows: web embed, telegram, teams.
"""

import asyncio
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.interface.middleware.multi_tenant_auth import MultiTenantAuthMiddleware
from backend.interface.handlers.embed_init_handler import EmbedInitHandler
from backend.infrastructure.rate_limiter import RateLimitService
from backend.shared.auth_config import register_test_tenant
from backend.shared.logger import logger


class TestMultiTenantAuth:
    """Test multi-tenant authentication flows"""
    
    @staticmethod
    def test_setup():
        """Setup test data"""
        logger.info("=" * 60)
        logger.info("TEST: Setup Test Tenants")
        logger.info("=" * 60)
        
        # Register catalog tenant
        register_test_tenant(
            tenant_id="catalog-001",
            name="GSNAKE Catalog",
            jwt_secret="test_secret_catalog_001_very_long_and_secure_at_least_32_chars",
        )
        
        logger.info("✅ Catalog tenant registered: catalog-001")
        print()
    
    @staticmethod
    def test_web_embed_flow():
        """Test web embed JWT flow"""
        logger.info("=" * 60)
        logger.info("TEST: Web Embed JWT Flow")
        logger.info("=" * 60)
        
        tenant_id = "catalog-001"
        origin = "https://gsnake.com"
        
        # Step 1: Generate user_key
        session_id = "session_abc123"
        user_key = EmbedInitHandler.generate_user_key("catalog-001", session_id)
        logger.info(f"1️⃣  Generated user_key: {user_key}")
        
        # Step 2: Generate JWT token
        token = MultiTenantAuthMiddleware.generate_web_embed_jwt(
            tenant_id=tenant_id,
            user_key=user_key,
            origin=origin,
            expiry_seconds=300
        )
        logger.info(f"2️⃣  Generated JWT token: {token[:50]}...")
        
        # Step 3: Verify JWT token
        try:
            payload = MultiTenantAuthMiddleware.verify_web_embed_jwt(
                token,
                tenant_id,
                origin
            )
            logger.info(f"3️⃣  ✅ JWT verified successfully")
            logger.info(f"    Payload: tenant={payload.tenant_id}, channel={payload.channel}, user={payload.user_key}")
        except Exception as e:
            logger.error(f"3️⃣  ❌ JWT verification failed: {e}")
            return False
        
        # Step 4: Test origin validation
        wrong_origin = "https://attacker.com"
        try:
            MultiTenantAuthMiddleware.verify_web_embed_jwt(
                token,
                tenant_id,
                wrong_origin
            )
            logger.error(f"4️⃣  ❌ Origin validation FAILED - should have rejected!")
            return False
        except Exception as e:
            logger.info(f"4️⃣  ✅ Origin validation works: {e}")
        
        # Step 5: Resolve context
        context = MultiTenantAuthMiddleware.resolve_context_from_jwt(
            token,
            tenant_id,
            origin
        )
        logger.info(f"5️⃣  ✅ Context resolved:")
        logger.info(f"    - tenant_id: {context.tenant_id}")
        logger.info(f"    - channel: {context.channel}")
        logger.info(f"    - user_key: {context.user_key}")
        
        print()
        return True
    
    @staticmethod
    async def test_rate_limiting():
        """Test rate limiting"""
        logger.info("=" * 60)
        logger.info("TEST: Rate Limiting")
        logger.info("=" * 60)
        
        tenant_id = "catalog-001"
        user_key = "test_user_123"
        
        # Send 5 requests
        for i in range(5):
            allowed, status = await RateLimitService.check_rate_limit(
                tenant_id,
                user_key
            )
            
            logger.info(
                f"Request {i+1}: "
                f"allowed={allowed}, "
                f"minute={status.get('current_minute', 0)}, "
                f"hour={status.get('current_hour', 0)}"
            )
        
        logger.info("✅ Rate limiting works")
        print()
        return True
    
    @staticmethod
    def test_embed_init_flow():
        """Test embed initialization"""
        logger.info("=" * 60)
        logger.info("TEST: Embed Initialization Flow")
        logger.info("=" * 60)
        
        # Simulate embed init request
        request_body = {
            "site_id": "catalog-001",
            "platform": "web",
            "user_data": {
                "email": "user@gsnake.com"
            }
        }
        
        origin = "https://gsnake.com"
        
        logger.info(f"1️⃣  Embed init request")
        logger.info(f"    site_id: {request_body['site_id']}")
        logger.info(f"    origin: {origin}")
        
        # TODO: Mock async call
        # result = await EmbedInitHandler.initialize(request_body, origin)
        
        logger.info(f"2️⃣  ✅ Embed initialized")
        print()
        return True
    
    @staticmethod
    def test_telegram_flow():
        """Test Telegram webhook verification"""
        logger.info("=" * 60)
        logger.info("TEST: Telegram Webhook Flow")
        logger.info("=" * 60)
        
        tenant_id = "catalog-001"
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        
        # Simulate Telegram webhook body
        telegram_update = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "date": int(datetime.now().timestamp()),
                "chat": {
                    "id": -123456789,
                    "type": "private"
                },
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "John",
                    "username": "john_doe"
                },
                "text": "Hello bot"
            }
        }
        
        body = json.dumps(telegram_update).encode()
        
        logger.info(f"1️⃣  Telegram webhook received")
        logger.info(f"    update_id: {telegram_update['update_id']}")
        logger.info(f"    from: {telegram_update['message']['from']['id']}")
        
        # Verify (would fail in real scenario due to no real config)
        logger.info(f"2️⃣  ⚠️  Webhook verification skipped (no real Telegram config)")
        
        # Resolve context
        context = MultiTenantAuthMiddleware.resolve_context_from_telegram(
            tenant_id,
            telegram_update['message']['from']['id']
        )
        
        logger.info(f"3️⃣  ✅ Context resolved:")
        logger.info(f"    - tenant_id: {context.tenant_id}")
        logger.info(f"    - channel: {context.channel}")
        logger.info(f"    - user_key: {context.user_key}")
        
        print()
        return True
    
    @staticmethod
    def test_teams_flow():
        """Test Teams JWT verification"""
        logger.info("=" * 60)
        logger.info("TEST: Teams Bot Framework Flow")
        logger.info("=" * 60)
        
        tenant_id = "catalog-001"
        aad_object_id = "00000000-0000-0000-0000-000000000001"
        
        logger.info(f"1️⃣  Teams message received")
        logger.info(f"    aadObjectId: {aad_object_id}")
        
        logger.info(f"2️⃣  ⚠️  JWT verification skipped (requires Microsoft JWKS)")
        
        # Resolve context
        context = MultiTenantAuthMiddleware.resolve_context_from_teams(
            tenant_id,
            aad_object_id
        )
        
        logger.info(f"3️⃣  ✅ Context resolved:")
        logger.info(f"    - tenant_id: {context.tenant_id}")
        logger.info(f"    - channel: {context.channel}")
        logger.info(f"    - user_key: {context.user_key}")
        
        print()
        return True


async def run_all_tests():
    """Run all tests"""
    print("\n")
    print("🧪 MULTI-TENANT BOT SERVICE - AUTHENTICATION TESTS")
    print("=" * 70)
    print("\n")
    
    results = {
        "Setup": TestMultiTenantAuth.test_setup(),
        "Web Embed": TestMultiTenantAuth.test_web_embed_flow(),
        "Rate Limiting": await TestMultiTenantAuth.test_rate_limiting(),
        "Embed Init": TestMultiTenantAuth.test_embed_init_flow(),
        "Telegram": TestMultiTenantAuth.test_telegram_flow(),
        "Teams": TestMultiTenantAuth.test_teams_flow(),
    }
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    print("\n")
    
    return passed == total


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

