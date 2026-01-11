"""
Seed Meta Domain Routing Data
Tạo routing data cho Meta domain (General/System intents)

Usage:
    # Seed data
    python -m backend.scripts.seed_meta_routing_data
    
    # Clean (delete) all seeded data
    python -m backend.scripts.seed_meta_routing_data --clean
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


async def seed_meta_routing_data():
    """Seed Meta domain routing data"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database")
        
        # Get admin user ID
        admin_service = AdminUserService()
        admin_user = await admin_service.get_admin_user_by_email("gsnake1102@gmail.com")
        admin_user_id = UUID(str(admin_user["id"]))
        
        # Create Meta routing data
        await create_meta_pattern_rules(admin_user_id)
        await create_meta_routing_rules(admin_user_id)
        await create_meta_prompt_templates(admin_user_id)
        
        # Wait for cache invalidation
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully seeded Meta domain routing data")
        print("\n✅ Đã tạo dữ liệu routing cho Meta domain thành công!")
        print("\n📝 Dữ liệu đã tạo:")
        print("   - Pattern rules: 2 rules (Meta intents)")
        print("   - Routing rules: 2 rules (Meta intents)")
        print("   - Prompt templates: 1 template (Meta prompt)")
        
    except Exception as e:
        logger.error(f"Error seeding Meta routing data: {e}", exc_info=True)
        print(f"\n❌ Error seeding Meta data: {e}")
        raise
    finally:
        await database_client.disconnect()


async def create_meta_pattern_rules(created_by: UUID):
    """Create Meta pattern rules"""
    from backend.schemas.admin_config_types import PatternRuleCreate
    
    pattern_rules = [
        {
            "rule_name": "Meta - Chào hỏi",
            "pattern_regex": r"^(?:chào|hello|hi|xin chào|hey|chào bạn|chào anh|chào chị)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "meta",
            "target_intent": "greeting",
            "intent_type": "META",
            "priority": 50,
            "description": "Chào hỏi",
        },
        {
            "rule_name": "Meta - Cảm ơn",
            "pattern_regex": r"^(?:cảm ơn|cám ơn|thanks|thank you|tks)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "meta",
            "target_intent": "thank_you",
            "intent_type": "META",
            "priority": 45,
            "description": "Cảm ơn",
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
    
    print(f"✅ Meta Pattern Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_meta_routing_rules(created_by: UUID):
    """Create Meta routing rules"""
    from backend.schemas.admin_config_types import RoutingRuleCreate
    
    routing_rules = [
        {
            "rule_name": "Meta - Chào hỏi",
            "intent_pattern": {"intent": "greeting", "match_type": "exact"},
            "target_domain": "meta",
            "priority": 50,
            "description": "Điều hướng chào hỏi đến Meta domain",
        },
        {
            "rule_name": "Meta - Cảm ơn",
            "intent_pattern": {"intent": "thank_you", "match_type": "exact"},
            "target_domain": "meta",
            "priority": 45,
            "description": "Điều hướng cảm ơn đến Meta domain",
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
    
    print(f"✅ Meta Routing Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_meta_prompt_templates(created_by: UUID):
    """Create Meta system prompt templates"""
    from backend.schemas.admin_config_types import PromptTemplateCreate
    
    prompt_templates = [
        {
            "rule_name": "Meta - Chào hỏi System Prompt",
            "template_name": "Meta - Chào hỏi System Prompt",
            "template_type": "system",
            "domain": "meta",
            "template_text": "Bạn là trợ lý thân thiện. Hãy chào hỏi người dùng một cách thân thiện và nhiệt tình. Trả lời bằng tiếng Việt.",
            "variables": {"required": [], "optional": ["user_name"]},
            "description": "System prompt cho chào hỏi",
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
    
    print(f"✅ Meta Prompt Templates - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def clean_meta_routing_data():
    """Delete all seeded Meta routing data"""
    try:
        await database_client.connect()
        logger.info("Connected to database")
        
        seeded_rules = {
            "Meta - Chào hỏi",
            "Meta - Cảm ơn",
        }
        
        seeded_routing = {
            "Meta - Chào hỏi",
            "Meta - Cảm ơn",
        }
        seeded_templates = {
            "Meta - Chào hỏi System Prompt",
        }
        
        deleted_counts = {
            "pattern_rules": 0,
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
        
        logger.info("✅ Successfully cleaned Meta routing data")
        print("\n✅ Đã xóa dữ liệu Meta routing thành công!")
        print("\n📝 Dữ liệu đã xóa:")
        print(f"   - Pattern rules: {deleted_counts['pattern_rules']} rules")
        print(f"   - Routing rules: {deleted_counts['routing_rules']} rules")
        print(f"   - Prompt templates: {deleted_counts['prompt_templates']} templates")
        
    except Exception as e:
        logger.error(f"Error cleaning Meta routing data: {e}", exc_info=True)
        print(f"\n❌ Error cleaning Meta data: {e}")
        raise
    finally:
        await database_client.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Meta domain routing data")
    parser.add_argument("--clean", action="store_true", help="Clean all seeded Meta routing data")
    args = parser.parse_args()
    
    if args.clean:
        asyncio.run(clean_meta_routing_data())
    else:
        asyncio.run(seed_meta_routing_data())
