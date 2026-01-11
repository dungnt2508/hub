"""
Seed Catalog Domain Routing Data
Tạo routing data cho Catalog domain

Usage:
    # Seed data
    python -m backend.scripts.seed_catalog_routing_data
    
    # Clean (delete) all seeded data
    python -m backend.scripts.seed_catalog_routing_data --clean
"""
import asyncio
import sys
import os
from uuid import UUID

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.infrastructure.database_client import database_client
from backend.domain.admin.admin_user_service import AdminUserService
from backend.domain.admin.admin_config_service import admin_config_service
from backend.shared.logger import logger


async def rule_exists(rule_name: str, list_func) -> bool:
    """Check if rule already exists by name to prevent duplicates"""
    try:
        existing = await list_func(limit=1000, offset=0)
        items = existing.get("items", [])
        for item in items:
            if hasattr(item, 'rule_name') and item.rule_name == rule_name:
                logger.debug(f"Rule already exists: {rule_name}")
                return True
        return False
    except Exception as e:
        logger.warning(f"Error checking if rule exists: {e}")
        return False


async def seed_catalog_routing_data():
    """Seed Catalog domain routing data"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database")
        
        # Get admin user ID
        admin_service = AdminUserService()
        admin_user = await admin_service.get_admin_user_by_email("gsnake1102@gmail.com")
        admin_user_id = UUID(str(admin_user["id"]))
        
        # Create Catalog routing data
        await create_catalog_pattern_rules(admin_user_id)
        await create_catalog_keyword_hints(admin_user_id)
        await create_catalog_routing_rules(admin_user_id)
        await create_catalog_prompt_templates(admin_user_id)
        
        # Wait for cache invalidation
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully seeded Catalog domain routing data")
        print("\n✅ Đã tạo dữ liệu routing cho Catalog domain thành công!")
        print("\n📝 Dữ liệu đã tạo:")
        print("   - Pattern rules: 2 rules (Catalog queries)")
        print("   - Keyword hints: 1 hint (Catalog keywords)")
        print("   - Routing rules: 2 rules (Catalog intents)")
        print("   - Prompt templates: 2 templates (Catalog prompts)")
        
    except Exception as e:
        logger.error(f"Error seeding Catalog routing data: {e}", exc_info=True)
        print(f"\n❌ Error seeding Catalog data: {e}")
        raise
    finally:
        await database_client.disconnect()


async def create_catalog_pattern_rules(created_by: UUID):
    """Create Catalog pattern rules"""
    from backend.schemas.admin_config_types import PatternRuleCreate
    
    pattern_rules = [
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm",
            "pattern_regex": r"(?:tìm|tìm kiếm|mua|bán|bán gì|mua gì|có gì)\s+(?:sản phẩm|hàng|đồ|món|sp)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "search_products",
            "intent_type": "KNOWLEDGE",
            "priority": 70,
            "description": "Tìm kiếm sản phẩm trong catalog",
        },
        {
            "rule_name": "Catalog - Xem giá sản phẩm",
            "pattern_regex": r"(?:giá|giá bao nhiêu|bao nhiêu tiền|giá cả)\s+(?:của|sản phẩm|món|hàng)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "query_price",
            "intent_type": "KNOWLEDGE",
            "priority": 65,
            "description": "Tra cứu giá sản phẩm",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for rule_data in pattern_rules:
        try:
            if await rule_exists(rule_data["rule_name"], admin_config_service.list_pattern_rules):
                logger.info(f"Pattern rule already exists, skipping: {rule_data['rule_name']}")
                skipped_count += 1
                continue
            
            rule = PatternRuleCreate(**rule_data)
            await admin_config_service.create_pattern_rule(rule=rule, created_by=created_by)
            created_count += 1
            logger.info(f"Created pattern rule: {rule_data['rule_name']}")
        except Exception as e:
            logger.warning(f"Failed to create pattern rule {rule_data['rule_name']}: {e}")
    
    print(f"✅ Catalog Pattern Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_catalog_keyword_hints(created_by: UUID):
    """Create Catalog keyword hints"""
    from backend.schemas.admin_config_types import KeywordHintCreate
    
    keyword_hints = [
        {
            "rule_name": "Catalog Domain - Từ khóa tiếng Việt",
            "domain": "catalog",
            "keywords": {
                "sản phẩm": 0.95,
                "hàng": 0.9,
                "món": 0.9,
                "đồ": 0.85,
                "mua": 0.85,
                "bán": 0.85,
                "giá": 0.8,
                "giá cả": 0.8,
                "giá tiền": 0.75,
                "tìm kiếm": 0.75,
                "tìm": 0.7,
                "catalog": 0.65,
                "danh mục": 0.65,
            },
            "description": "Từ khóa cho domain Catalog (Danh mục sản phẩm)",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for hint_data in keyword_hints:
        try:
            if await rule_exists(hint_data["rule_name"], admin_config_service.list_keyword_hints):
                logger.info(f"Keyword hint already exists, skipping: {hint_data['rule_name']}")
                skipped_count += 1
                continue
            
            hint = KeywordHintCreate(**hint_data)
            await admin_config_service.create_keyword_hint(hint=hint, created_by=created_by)
            created_count += 1
            logger.info(f"Created keyword hint: {hint_data['rule_name']}")
        except Exception as e:
            logger.warning(f"Failed to create keyword hint {hint_data['rule_name']}: {e}")
    
    print(f"✅ Catalog Keyword Hints - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_catalog_routing_rules(created_by: UUID):
    """Create Catalog routing rules"""
    from backend.schemas.admin_config_types import RoutingRuleCreate
    
    routing_rules = [
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm",
            "intent_pattern": {"intent": "search_products", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 80,
            "description": "Điều hướng tìm kiếm sản phẩm đến domain Catalog",
        },
        {
            "rule_name": "Catalog - Tra cứu giá",
            "intent_pattern": {"intent": "query_price", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 75,
            "description": "Điều hướng tra cứu giá sản phẩm đến domain Catalog",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for rule_data in routing_rules:
        try:
            if await rule_exists(rule_data["rule_name"], admin_config_service.list_routing_rules):
                logger.info(f"Routing rule already exists, skipping: {rule_data['rule_name']}")
                skipped_count += 1
                continue
            
            rule = RoutingRuleCreate(**rule_data)
            await admin_config_service.create_routing_rule(rule=rule, created_by=created_by)
            created_count += 1
            logger.info(f"Created routing rule: {rule_data['rule_name']}")
        except Exception as e:
            logger.warning(f"Failed to create routing rule {rule_data['rule_name']}: {e}")
    
    print(f"✅ Catalog Routing Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_catalog_prompt_templates(created_by: UUID):
    """Create Catalog system prompt templates"""
    from backend.schemas.admin_config_types import PromptTemplateCreate
    
    prompt_templates = [
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm System Prompt",
            "template_name": "Catalog - Tìm kiếm sản phẩm System Prompt",
            "template_type": "system",
            "domain": "catalog",
            "template_text": "Bạn là trợ lý tìm kiếm sản phẩm. Hãy giúp người dùng tìm kiếm sản phẩm trong danh mục. Hỏi thêm thông tin nếu cần. Trả lời bằng tiếng Việt.",
            "variables": {"required": [], "optional": ["search_query", "category", "price_range"]},
            "description": "System prompt cho tìm kiếm sản phẩm",
        },
        {
            "rule_name": "Catalog - Tra cứu giá System Prompt",
            "template_name": "Catalog - Tra cứu giá System Prompt",
            "template_type": "system",
            "domain": "catalog",
            "template_text": "Bạn là trợ lý tra cứu giá. Hãy giúp người dùng tra cứu giá sản phẩm. Hiển thị giá rõ ràng và đầy đủ. Trả lời bằng tiếng Việt.",
            "variables": {"required": ["product_name"], "optional": ["product_id", "category"]},
            "description": "System prompt cho tra cứu giá sản phẩm",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for template_data in prompt_templates:
        try:
            if await rule_exists(template_data["rule_name"], admin_config_service.list_prompt_templates):
                logger.info(f"Prompt template already exists, skipping: {template_data['rule_name']}")
                skipped_count += 1
                continue
            
            template = PromptTemplateCreate(**template_data)
            await admin_config_service.create_prompt_template(template=template, created_by=created_by)
            created_count += 1
            logger.info(f"Created prompt template: {template_data['template_name']}")
        except Exception as e:
            logger.warning(f"Failed to create prompt template {template_data['template_name']}: {e}")
    
    print(f"✅ Catalog Prompt Templates - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def clean_catalog_routing_data():
    """Delete all seeded Catalog routing data"""
    try:
        await database_client.connect()
        logger.info("Connected to database")
        
        seeded_rules = {
            "Catalog - Tìm kiếm sản phẩm",
            "Catalog - Xem giá sản phẩm",
        }
        
        seeded_hints = {"Catalog Domain - Từ khóa tiếng Việt"}
        seeded_routing = {
            "Catalog - Tìm kiếm sản phẩm",
            "Catalog - Tra cứu giá",
        }
        seeded_templates = {
            "Catalog - Tìm kiếm sản phẩm System Prompt",
            "Catalog - Tra cứu giá System Prompt",
        }
        
        deleted_counts = {
            "pattern_rules": 0,
            "keyword_hints": 0,
            "routing_rules": 0,
            "prompt_templates": 0,
        }
        
        # Delete pattern rules
        try:
            rules = await admin_config_service.list_pattern_rules(limit=1000, offset=0)
            for rule in rules.get("items", []):
                if hasattr(rule, 'rule_name') and rule.rule_name in seeded_rules:
                    try:
                        await admin_config_service.delete_pattern_rule(rule.id)
                        deleted_counts["pattern_rules"] += 1
                        logger.info(f"Deleted pattern rule: {rule.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete pattern rule {rule.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting pattern rules: {e}")
        
        # Delete keyword hints
        try:
            hints = await admin_config_service.list_keyword_hints(limit=1000, offset=0)
            for hint in hints.get("items", []):
                if hasattr(hint, 'rule_name') and hint.rule_name in seeded_hints:
                    try:
                        await admin_config_service.delete_keyword_hint(hint.id)
                        deleted_counts["keyword_hints"] += 1
                        logger.info(f"Deleted keyword hint: {hint.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete keyword hint {hint.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting keyword hints: {e}")
        
        # Delete routing rules
        try:
            rules = await admin_config_service.list_routing_rules(limit=1000, offset=0)
            for rule in rules.get("items", []):
                if hasattr(rule, 'rule_name') and rule.rule_name in seeded_routing:
                    try:
                        await admin_config_service.delete_routing_rule(rule.id)
                        deleted_counts["routing_rules"] += 1
                        logger.info(f"Deleted routing rule: {rule.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete routing rule {rule.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting routing rules: {e}")
        
        # Delete templates
        try:
            templates = await admin_config_service.list_prompt_templates(limit=1000, offset=0)
            for template in templates.get("items", []):
                if hasattr(template, 'rule_name') and template.rule_name in seeded_templates:
                    try:
                        await admin_config_service.delete_prompt_template(template.id)
                        deleted_counts["prompt_templates"] += 1
                        logger.info(f"Deleted prompt template: {template.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete prompt template {template.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting prompt templates: {e}")
        
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully cleaned Catalog routing data")
        print("\n✅ Đã xóa dữ liệu Catalog routing thành công!")
        print("\n📝 Dữ liệu đã xóa:")
        print(f"   - Pattern rules: {deleted_counts['pattern_rules']} rules")
        print(f"   - Keyword hints: {deleted_counts['keyword_hints']} hints")
        print(f"   - Routing rules: {deleted_counts['routing_rules']} rules")
        print(f"   - Prompt templates: {deleted_counts['prompt_templates']} templates")
        
    except Exception as e:
        logger.error(f"Error cleaning Catalog routing data: {e}", exc_info=True)
        print(f"\n❌ Error cleaning Catalog data: {e}")
        raise
    finally:
        await database_client.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Catalog domain routing data")
    parser.add_argument("--clean", action="store_true", help="Clean all seeded Catalog routing data")
    args = parser.parse_args()
    
    if args.clean:
        asyncio.run(clean_catalog_routing_data())
    else:
        asyncio.run(seed_catalog_routing_data())
