"""
Seed HR Domain Routing Data
Tạo routing data cho HR domain

Usage:
    # Seed data
    python -m backend.scripts.seed_hr_routing_data
    
    # Clean (delete) all seeded data
    python -m backend.scripts.seed_hr_routing_data --clean
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


async def seed_hr_routing_data():
    """Seed HR domain routing data"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database")
        
        # Get admin user ID
        admin_service = AdminUserService()
        admin_user = await admin_service.get_admin_user_by_email("gsnake1102@gmail.com")
        admin_user_id = UUID(str(admin_user["id"]))
        
        # Create HR routing data
        await create_hr_pattern_rules(admin_user_id)
        await create_hr_keyword_hints(admin_user_id)
        await create_hr_routing_rules(admin_user_id)
        await create_hr_prompt_templates(admin_user_id)
        
        # Wait for cache invalidation
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully seeded HR domain routing data")
        print("\n✅ Đã tạo dữ liệu routing cho HR domain thành công!")
        print("\n📝 Dữ liệu đã tạo:")
        print("   - Pattern rules: 4 rules (HR queries)")
        print("   - Keyword hints: 1 hint (HR keywords)")
        print("   - Routing rules: 3 rules (HR intents)")
        print("   - Prompt templates: 3 templates (HR prompts)")
        
    except Exception as e:
        logger.error(f"Error seeding HR routing data: {e}", exc_info=True)
        print(f"\n❌ Error seeding HR data: {e}")
        raise
    finally:
        await database_client.disconnect()


async def create_hr_pattern_rules(created_by: UUID):
    """Create HR pattern rules"""
    from backend.schemas.admin_config_types import PatternRuleCreate
    
    pattern_rules = [
        {
            "rule_name": "HR - Tra cứu số ngày phép",
            "pattern_regex": r"(?:tôi|mình|em|tớ|anh|chị)\s+(?:còn|đang có|có)\s+(?:bao nhiêu|mấy)\s+(?:ngày|ngày phép|ngày nghỉ|ngày nghỉ phép)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "hr",
            "target_intent": "query_leave_balance",
            "intent_type": "OPERATION",
            "priority": 100,
            "description": "Tra cứu số ngày phép còn lại",
        },
        {
            "rule_name": "HR - Xin nghỉ phép",
            "pattern_regex": r"(?:xin|đăng ký|tạo|tạo đơn|làm đơn)\s+(?:nghỉ phép|nghỉ|phép|nghỉ việc)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "hr",
            "target_intent": "create_leave_request",
            "intent_type": "OPERATION",
            "priority": 90,
            "description": "Tạo đơn xin nghỉ phép",
        },
        {
            "rule_name": "HR - Duyệt đơn nghỉ phép",
            "pattern_regex": r"(?:duyệt|chấp nhận|đồng ý|phê duyệt)\s+(?:đơn nghỉ phép|đơn phép|đơn xin nghỉ)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "hr",
            "target_intent": "approve_leave",
            "intent_type": "OPERATION",
            "priority": 80,
            "description": "Duyệt đơn nghỉ phép",
        },
        {
            "rule_name": "HR - Tra cứu lương",
            "pattern_regex": r"(?:lương|tiền lương|thu nhập|bảng lương)\s+(?:tháng|này|năm|bao nhiêu)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "hr",
            "target_intent": "query_salary",
            "intent_type": "OPERATION",
            "priority": 75,
            "description": "Tra cứu thông tin lương",
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
    
    print(f"✅ HR Pattern Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_hr_keyword_hints(created_by: UUID):
    """Create HR keyword hints"""
    from backend.schemas.admin_config_types import KeywordHintCreate
    
    keyword_hints = [
        {
            "rule_name": "HR Domain - Từ khóa tiếng Việt",
            "domain": "hr",
            "keywords": {
                "nghỉ phép": 0.95,
                "ngày phép": 0.95,
                "phép": 0.9,
                "nghỉ việc": 0.85,
                "xin nghỉ": 0.85,
                "đơn nghỉ": 0.85,
                "duyệt đơn": 0.8,
                "lương": 0.8,
                "tiền lương": 0.8,
                "bảng lương": 0.75,
                "nhân viên": 0.7,
                "nhân sự": 0.7,
                "hr": 0.65,
            },
            "description": "Từ khóa cho domain HR (Nhân sự)",
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
    
    print(f"✅ HR Keyword Hints - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_hr_routing_rules(created_by: UUID):
    """Create HR routing rules"""
    from backend.schemas.admin_config_types import RoutingRuleCreate
    
    routing_rules = [
        {
            "rule_name": "HR - Tra cứu ngày phép",
            "intent_pattern": {"intent": "query_leave_balance", "match_type": "exact"},
            "target_domain": "hr",
            "priority": 100,
            "description": "Điều hướng câu hỏi tra cứu ngày phép đến domain HR",
        },
        {
            "rule_name": "HR - Tạo đơn nghỉ phép",
            "intent_pattern": {"intent": "create_leave_request", "match_type": "exact"},
            "target_domain": "hr",
            "priority": 90,
            "description": "Điều hướng yêu cầu tạo đơn nghỉ phép đến domain HR",
        },
        {
            "rule_name": "HR - Duyệt đơn nghỉ phép",
            "intent_pattern": {"intent": "approve_leave", "match_type": "exact"},
            "target_domain": "hr",
            "priority": 85,
            "description": "Điều hướng yêu cầu duyệt đơn nghỉ phép đến domain HR",
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
    
    print(f"✅ HR Routing Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_hr_prompt_templates(created_by: UUID):
    """Create HR system prompt templates"""
    from backend.schemas.admin_config_types import PromptTemplateCreate
    
    prompt_templates = [
        {
            "rule_name": "HR - Tra cứu ngày phép System Prompt",
            "template_name": "HR - Tra cứu ngày phép System Prompt",
            "template_type": "system",
            "domain": "hr",
            "template_text": "Bạn là trợ lý nhân sự. Hãy giúp nhân viên tra cứu số ngày phép còn lại. Hãy thân thiện và chuyên nghiệp. Trả lời bằng tiếng Việt.",
            "variables": {"required": [], "optional": ["employee_name", "leave_balance"]},
            "description": "System prompt cho tra cứu ngày phép",
        },
        {
            "rule_name": "HR - Tạo đơn nghỉ phép System Prompt",
            "template_name": "HR - Tạo đơn nghỉ phép System Prompt",
            "template_type": "system",
            "domain": "hr",
            "template_text": "Bạn là trợ lý nhân sự. Hãy giúp nhân viên tạo đơn xin nghỉ phép. Cần thu thập thông tin: ngày bắt đầu, ngày kết thúc, và lý do nghỉ. Trả lời bằng tiếng Việt.",
            "variables": {"required": ["start_date", "end_date", "reason"], "optional": ["employee_name"]},
            "description": "System prompt cho tạo đơn nghỉ phép",
        },
        {
            "rule_name": "HR - Duyệt đơn nghỉ phép System Prompt",
            "template_name": "HR - Duyệt đơn nghỉ phép System Prompt",
            "template_type": "system",
            "domain": "hr",
            "template_text": "Bạn là trợ lý nhân sự. Hãy giúp quản lý duyệt đơn nghỉ phép. Chỉ quản lý và admin mới có quyền duyệt. Trả lời bằng tiếng Việt.",
            "variables": {"required": ["leave_request_id"], "optional": ["approver_name"]},
            "description": "System prompt cho duyệt đơn nghỉ phép",
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
    
    print(f"✅ HR Prompt Templates - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def clean_hr_routing_data():
    """Delete all seeded HR routing data"""
    try:
        await database_client.connect()
        logger.info("Connected to database")
        
        seeded_rules = {
            "HR - Tra cứu số ngày phép",
            "HR - Xin nghỉ phép",
            "HR - Duyệt đơn nghỉ phép",
            "HR - Tra cứu lương",
        }
        
        seeded_hints = {"HR Domain - Từ khóa tiếng Việt"}
        seeded_routing = {
            "HR - Tra cứu ngày phép",
            "HR - Tạo đơn nghỉ phép",
            "HR - Duyệt đơn nghỉ phép",
        }
        seeded_templates = {
            "HR - Tra cứu ngày phép System Prompt",
            "HR - Tạo đơn nghỉ phép System Prompt",
            "HR - Duyệt đơn nghỉ phép System Prompt",
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
        
        logger.info("✅ Successfully cleaned HR routing data")
        print("\n✅ Đã xóa dữ liệu HR routing thành công!")
        print("\n📝 Dữ liệu đã xóa:")
        print(f"   - Pattern rules: {deleted_counts['pattern_rules']} rules")
        print(f"   - Keyword hints: {deleted_counts['keyword_hints']} hints")
        print(f"   - Routing rules: {deleted_counts['routing_rules']} rules")
        print(f"   - Prompt templates: {deleted_counts['prompt_templates']} templates")
        
    except Exception as e:
        logger.error(f"Error cleaning HR routing data: {e}", exc_info=True)
        print(f"\n❌ Error cleaning HR data: {e}")
        raise
    finally:
        await database_client.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed HR domain routing data")
    parser.add_argument("--clean", action="store_true", help="Clean all seeded HR routing data")
    args = parser.parse_args()
    
    if args.clean:
        asyncio.run(clean_hr_routing_data())
    else:
        asyncio.run(seed_hr_routing_data())
