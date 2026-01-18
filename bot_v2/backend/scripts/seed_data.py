"""Seed data script for bot_v2

Script này tạo dữ liệu mẫu cho development và testing.
Chạy script: python -m backend.scripts.seed_data
"""
import asyncio
import sys
import json
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from backend.database import AsyncSessionLocal
from backend.config import settings


async def seed_data():
    """Seed database with sample data"""
    async with AsyncSessionLocal() as session:
        try:
            print("🌱 Bắt đầu seed data...")
            
            # 1. Create Tenants
            print("\n📦 Tạo Tenants...")
            tenant_1_id = uuid4()
            tenant_2_id = uuid4()
            
            await session.execute(text("""
                INSERT INTO tenants (id, name, status, plan, settings_version, created_at, updated_at)
                VALUES 
                    (:id1, :name1, :status1, :plan1, :version1, :created_at, :updated_at),
                    (:id2, :name2, :status2, :plan2, :version2, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": tenant_1_id,
                "name1": "Demo Company",
                "status1": "active",
                "plan1": "premium",
                "version1": 1,
                "id2": tenant_2_id,
                "name2": "Test Tenant",
                "status2": "active",
                "plan2": "basic",
                "version2": 1,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # 2. Create Channels
            print("📡 Tạo Channels...")
            channel_1_id = uuid4()
            channel_2_id = uuid4()
            
            await session.execute(text("""
                INSERT INTO channels (id, tenant_id, type, enabled, config_json, created_at, updated_at)
                VALUES 
                    (:id1, :tenant_id1, :type1, :enabled1, CAST(:config1 AS jsonb), :created_at, :updated_at),
                    (:id2, :tenant_id1, :type2, :enabled2, CAST(:config2 AS jsonb), :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": channel_1_id,
                "tenant_id1": tenant_1_id,
                "type1": "telegram",
                "enabled1": True,
                "config1": json.dumps({"bot_token": "demo_token", "webhook_url": "https://example.com/webhook"}),
                "id2": channel_2_id,
                "type2": "web",
                "enabled2": True,
                "config2": json.dumps({"embed_id": "demo_embed"}),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # 3. Create Products
            print("🛍️ Tạo Products...")
            product_1_id = uuid4()
            product_2_id = uuid4()
            product_3_id = uuid4()
            
            await session.execute(text("""
                INSERT INTO products (id, tenant_id, sku, slug, name, category, status, created_at, updated_at)
                VALUES 
                    (:id1, :tenant_id, :sku1, :slug1, :name1, :category1, :status, :created_at, :updated_at),
                    (:id2, :tenant_id, :sku2, :slug2, :name2, :category2, :status, :created_at, :updated_at),
                    (:id3, :tenant_id, :sku3, :slug3, :name3, :category3, :status, :created_at, :updated_at)
                ON CONFLICT (tenant_id, sku) DO NOTHING
            """), {
                "id1": product_1_id,
                "id2": product_2_id,
                "id3": product_3_id,
                "tenant_id": tenant_1_id,
                "sku1": "PROD-001",
                "slug1": "laptop-dell-xps-15",
                "name1": "Laptop Dell XPS 15",
                "category1": "Electronics",
                "sku2": "PROD-002",
                "slug2": "iphone-15-pro",
                "name2": "iPhone 15 Pro",
                "category2": "Electronics",
                "sku3": "PROD-003",
                "slug3": "wireless-headphones",
                "name3": "Wireless Headphones Premium",
                "category3": "Audio",
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # 4. Create Product Attributes
            print("📋 Tạo Product Attributes...")
            await session.execute(text("""
                INSERT INTO product_attributes (id, tenant_id, product_id, attributes_key, attributes_value, attributes_value_type, created_at)
                VALUES 
                    (:id1, :tenant_id, :product_id1, :key1, :value1, :type1, :created_at),
                    (:id2, :tenant_id, :product_id1, :key2, :value2, :type2, :created_at),
                    (:id3, :tenant_id, :product_id1, :key3, :value3, :type3, :created_at),
                    (:id4, :tenant_id, :product_id2, :key4, :value4, :type2, :created_at),
                    (:id5, :tenant_id, :product_id2, :key5, :value5, :type2, :created_at),
                    (:id6, :tenant_id, :product_id3, :key6, :value6, :type2, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "id3": uuid4(),
                "id4": uuid4(),
                "id5": uuid4(),
                "id6": uuid4(),
                "tenant_id": tenant_1_id,
                "product_id1": product_1_id,
                "key1": "price",
                "value1": "25000000",
                "type1": "number",
                "key2": "brand",
                "value2": "Dell",
                "type2": "string",
                "key3": "ram",
                "value3": "16GB",
                "type3": "string",
                "product_id2": product_2_id,
                "key4": "price",
                "value4": "30000000",
                "key5": "storage",
                "value5": "256GB",
                "product_id3": product_3_id,
                "key6": "price",
                "value6": "5000000",
                "created_at": datetime.now(timezone.utc),
            })
            
            # 5. Create Use Cases
            print("💼 Tạo Use Cases...")
            await session.execute(text("""
                INSERT INTO use_cases (id, tenant_id, product_id, type, description, created_at)
                VALUES 
                    (:id1, :tenant_id, :product_id1, :type1, :desc1, :created_at),
                    (:id2, :tenant_id, :product_id1, :type1, :desc2, :created_at),
                    (:id3, :tenant_id, :product_id2, :type1, :desc3, :created_at),
                    (:id4, :tenant_id, :product_id3, :type2, :desc4, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "id3": uuid4(),
                "id4": uuid4(),
                "tenant_id": tenant_1_id,
                "product_id1": product_1_id,
                "type1": "allowed",
                "desc1": "Phù hợp cho công việc văn phòng và học tập",
                "desc2": "Có thể chơi game nhẹ và chỉnh sửa video cơ bản",
                "product_id2": product_2_id,
                "desc3": "Phù hợp cho chụp ảnh và quay video chất lượng cao",
                "product_id3": product_3_id,
                "type2": "disallowed",
                "desc4": "Không phù hợp cho môi trường ồn ào công nghiệp",
                "created_at": datetime.now(timezone.utc),
            })
            
            # 6. Create FAQs
            print("❓ Tạo FAQs...")
            await session.execute(text("""
                INSERT INTO faqs (id, tenant_id, scope, product_id, question, answer, created_at, updated_at)
                VALUES 
                    (:id1, :tenant_id, :scope1, NULL, :q1, :a1, :created_at, :updated_at),
                    (:id2, :tenant_id, :scope2, :product_id1, :q2, :a2, :created_at, :updated_at),
                    (:id3, :tenant_id, :scope2, :product_id2, :q3, :a3, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "id3": uuid4(),
                "tenant_id": tenant_1_id,
                "scope1": "global",
                "q1": "Làm thế nào để đặt hàng?",
                "a1": "Bạn có thể đặt hàng qua website hoặc liên hệ hotline 1900-xxxx",
                "scope2": "product",
                "product_id1": product_1_id,
                "q2": "Laptop Dell XPS 15 có bảo hành bao lâu?",
                "a2": "Sản phẩm có bảo hành chính hãng 12 tháng",
                "product_id2": product_2_id,
                "q3": "iPhone 15 Pro có hỗ trợ 5G không?",
                "a3": "Có, iPhone 15 Pro hỗ trợ đầy đủ các băng tần 5G",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # 7. Create Comparisons
            print("⚖️ Tạo Comparisons...")
            await session.execute(text("""
                INSERT INTO comparisons (id, tenant_id, product_a, product_b, allowed_attributes, created_at)
                VALUES 
                    (:id1, :tenant_id, :product_a, :product_b, CAST(:attrs AS jsonb), :created_at)
                ON CONFLICT (tenant_id, product_a, product_b) DO NOTHING
            """), {
                "id1": uuid4(),
                "tenant_id": tenant_1_id,
                "product_a": product_1_id,
                "product_b": product_2_id,
                "attrs": json.dumps(["price", "brand", "ram"]),
                "created_at": datetime.now(timezone.utc),
            })
            
            # 8. Create Guardrails
            print("🛡️ Tạo Guardrails...")
            await session.execute(text("""
                INSERT INTO guardrails (id, tenant_id, forbidden_topics, disclaimers, fallback_message, created_at, updated_at)
                VALUES 
                    (:id1, :tenant_id, CAST(:forbidden AS jsonb), CAST(:disclaimers AS jsonb), :fallback, :created_at, :updated_at)
                ON CONFLICT (tenant_id) DO NOTHING
            """), {
                "id1": uuid4(),
                "tenant_id": tenant_1_id,
                "forbidden": json.dumps(["chính trị", "tôn giáo", "nội dung nhạy cảm"]),
                "disclaimers": json.dumps(["Thông tin giá có thể thay đổi", "Sản phẩm có thể hết hàng"]),
                "fallback": "Xin lỗi, tôi không thể trả lời câu hỏi này. Vui lòng liên hệ bộ phận hỗ trợ.",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # 9. Create Intents
            print("🎯 Tạo Intents...")
            intent_1_id = uuid4()
            intent_2_id = uuid4()
            intent_3_id = uuid4()
            
            await session.execute(text("""
                INSERT INTO intents (id, tenant_id, name, domain, priority, created_at, updated_at)
                VALUES 
                    (:id1, :tenant_id, :name1, :domain1, :priority1, :created_at, :updated_at),
                    (:id2, :tenant_id, :name2, :domain2, :priority2, :created_at, :updated_at),
                    (:id3, :tenant_id, :name3, :domain3, :priority3, :created_at, :updated_at)
                ON CONFLICT (tenant_id, name) DO NOTHING
            """), {
                "id1": intent_1_id,
                "id2": intent_2_id,
                "id3": intent_3_id,
                "tenant_id": tenant_1_id,
                "name1": "ask_price",
                "domain1": "product",
                "priority1": 10,
                "name2": "compare_products",
                "domain2": "product",
                "priority2": 8,
                "name3": "ask_suitability",
                "domain3": "product",
                "priority3": 5,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # 10. Create Intent Patterns
            print("🔍 Tạo Intent Patterns...")
            await session.execute(text("""
                INSERT INTO intent_patterns (id, intent_id, type, pattern, weight, created_at)
                VALUES 
                    (:id1, :intent_id1, :type1, :pattern1, :weight1, :created_at),
                    (:id2, :intent_id1, :type1, :pattern2, :weight2, :created_at),
                    (:id3, :intent_id2, :type1, :pattern3, :weight1, :created_at),
                    (:id4, :intent_id3, :type1, :pattern4, :weight1, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "id3": uuid4(),
                "id4": uuid4(),
                "intent_id1": intent_1_id,
                "type1": "keyword",
                "pattern1": "giá",
                "weight1": 1.0,
                "pattern2": "bao nhiêu tiền",
                "weight2": 0.9,
                "intent_id2": intent_2_id,
                "pattern3": "so sánh",
                "intent_id3": intent_3_id,
                "pattern4": "phù hợp",
                "created_at": datetime.now(timezone.utc),
            })
            
            # 11. Create Intent Hints
            print("💡 Tạo Intent Hints...")
            await session.execute(text("""
                INSERT INTO intent_hints (id, intent_id, hint_text, created_at)
                VALUES 
                    (:id1, :intent_id1, :hint1, :created_at),
                    (:id2, :intent_id2, :hint2, :created_at),
                    (:id3, :intent_id3, :hint3, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "id3": uuid4(),
                "intent_id1": intent_1_id,
                "hint1": "User đang hỏi về giá sản phẩm",
                "intent_id2": intent_2_id,
                "hint2": "User muốn so sánh các sản phẩm",
                "intent_id3": intent_3_id,
                "hint3": "User muốn biết sản phẩm có phù hợp không",
                "created_at": datetime.now(timezone.utc),
            })
            
            # 12. Create Intent Actions
            print("⚡ Tạo Intent Actions...")
            await session.execute(text("""
                INSERT INTO intent_actions (id, intent_id, action_type, config_json, priority, created_at)
                VALUES 
                    (:id1, :intent_id1, :action_type1, CAST(:config1 AS jsonb), :priority1, :created_at),
                    (:id2, :intent_id2, :action_type2, CAST(:config2 AS jsonb), :priority2, :created_at),
                    (:id3, :intent_id3, :action_type3, CAST(:config3 AS jsonb), :priority3, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "id3": uuid4(),
                "intent_id1": intent_1_id,
                "action_type1": "query_db",
                "config1": json.dumps({"handler": "product_price"}),
                "priority1": 10,
                "intent_id2": intent_2_id,
                "action_type2": "query_db",
                "config2": json.dumps({"handler": "product_comparison"}),
                "priority2": 10,
                "intent_id3": intent_3_id,
                "action_type3": "query_db",
                "config3": json.dumps({"handler": "product_suitability"}),
                "priority3": 10,
                "created_at": datetime.now(timezone.utc),
            })
            
            # 13. Create Migration Jobs
            print("🔄 Tạo Migration Jobs...")
            await session.execute(text("""
                INSERT INTO migration_jobs (id, tenant_id, source_type, status, created_at, updated_at)
                VALUES 
                    (:id1, :tenant_id, :source_type1, :status1, :created_at, :updated_at),
                    (:id2, :tenant_id, :source_type2, :status2, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "tenant_id": tenant_1_id,
                "source_type1": "excel",
                "status1": "completed",
                "source_type2": "cms",
                "status2": "pending",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # 14. Create Conversation Logs
            print("📝 Tạo Conversation Logs...")
            await session.execute(text("""
                INSERT INTO conversation_logs (id, tenant_id, channel_id, intent, domain, success, created_at)
                VALUES 
                    (:id1, :tenant_id, :channel_id, :intent1, :domain1, :success1, :created_at),
                    (:id2, :tenant_id, :channel_id, :intent2, :domain2, :success2, :created_at),
                    (:id3, :tenant_id, :channel_id, NULL, NULL, :success3, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "id3": uuid4(),
                "tenant_id": tenant_1_id,
                "channel_id": channel_1_id,
                "intent1": "ask_price",
                "domain1": "product",
                "success1": True,
                "intent2": "compare_products",
                "domain2": "product",
                "success2": True,
                "success3": False,
                "created_at": datetime.now(timezone.utc),
            })
            
            # 15. Create Failed Queries
            print("❌ Tạo Failed Queries...")
            await session.execute(text("""
                INSERT INTO failed_queries (id, tenant_id, query, reason, created_at)
                VALUES 
                    (:id1, :tenant_id, :query1, :reason1, :created_at),
                    (:id2, :tenant_id, :query2, :reason2, :created_at)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id1": uuid4(),
                "id2": uuid4(),
                "tenant_id": tenant_1_id,
                "query1": "What is the meaning of life?",
                "reason1": "No intent matched",
                "query2": "Tell me a joke",
                "reason2": "Guardrail violation - off-topic",
                "created_at": datetime.now(timezone.utc),
            })
            
            await session.commit()
            print("\n✅ Seed data hoàn tất!")
            print(f"\n📊 Tóm tắt:")
            print(f"   - Tenants: 2")
            print(f"   - Channels: 2")
            print(f"   - Products: 3")
            print(f"   - Intents: 3")
            print(f"   - Migration Jobs: 2")
            print(f"\n💡 Tenant ID để test: {tenant_1_id}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Lỗi khi seed data: {e}")
            raise


if __name__ == "__main__":
    print(f"🔗 Database URL: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'hidden'}")
    asyncio.run(seed_data())
