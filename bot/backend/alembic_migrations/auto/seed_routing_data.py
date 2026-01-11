"""
Seed Admin Dashboard Data
Tạo sample data cho admin dashboard frontend

Usage:
    # Seed data
    python -m backend.scripts.seed_admin_data
    
    # Clean (delete) all seeded data
    python -m backend.scripts.seed_admin_data --clean
"""
import asyncio
import sys
import os
from uuid import UUID, uuid4
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.infrastructure.database_client import database_client
from backend.domain.admin.admin_user_service import AdminUserService
from backend.domain.admin.admin_config_service import admin_config_service
from backend.shared.logger import logger


async def seed_admin_data():
    """Seed admin dashboard with sample data"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database")
        
        # 1. Create admin user if not exists
        # await create_admin_user()
        
        # 2. Get admin user ID for created_by
        admin_service = AdminUserService()
        admin_user = await admin_service.get_admin_user_by_email("gsnake1102@gmail.com")
        admin_user_id = UUID(str(admin_user["id"]))
        
        # 3. Create sample pattern rules
        await create_pattern_rules(admin_user_id)
        
        # 4. Create sample keyword hints
        await create_keyword_hints(admin_user_id)
        
        # 5. Create sample routing rules
        await create_routing_rules(admin_user_id)
        
        # 6. Create sample prompt templates
        await create_prompt_templates(admin_user_id)
        
        # Wait a bit for cache invalidation
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully seeded admin dashboard data")
        print("\n✅ Đã tạo dữ liệu mẫu cho admin dashboard thành công!")
        print("\n📝 Dữ liệu đã tạo:")
        print("   - Admin user: admin@example.com / admin123")
        print("   - Pattern rules: 8 rules (tối ưu cho tiếng Việt)")
        print("   - Keyword hints: 3 domains (từ khóa tiếng Việt)")
        print("   - Routing rules: 5 rules")
        print("   - Prompt templates: 7 templates (tiếng Việt)")
        
    except Exception as e:
        logger.error(f"Error seeding admin data: {e}", exc_info=True)
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        await database_client.disconnect()


async def create_admin_user():
    """Create default admin user"""
    try:
        admin_service = AdminUserService()
        await admin_service.get_admin_user_by_email("admin@example.com")
        logger.info("Admin user already exists, skipping creation")
        print("ℹ️  Admin user đã tồn tại, bỏ qua")
    except Exception:
        # User doesn't exist, create it
        await admin_service.create_admin_user(
            email="admin@example.com",
            password="admin123",
            role="admin",
            tenant_id=None,
        )
        logger.info("Created admin user: admin@example.com")
        print("✅ Đã tạo admin user: admin@example.com / admin123")


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


async def create_pattern_rules(created_by: UUID):
    """Create sample pattern rules"""
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
        {
            "rule_name": "Chào hỏi",
            "pattern_regex": r"^(?:chào|hello|hi|xin chào|hey|chào bạn|chào anh|chào chị)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "meta",
            "target_intent": "greeting",
            "intent_type": "META",
            "priority": 50,
            "description": "Chào hỏi",
        },
        {
            "rule_name": "Cảm ơn",
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
            # Check if rule already exists to prevent duplicates
            if await rule_exists(rule_data["rule_name"], admin_config_service.list_pattern_rules):
                logger.info(f"Pattern rule already exists, skipping: {rule_data['rule_name']}")
                skipped_count += 1
                continue
            
            rule = PatternRuleCreate(**rule_data)
            await admin_config_service.create_pattern_rule(
                rule=rule,
                created_by=created_by,
            )
            created_count += 1
            logger.info(f"Created pattern rule: {rule_data['rule_name']}")
        except Exception as e:
            logger.warning(f"Failed to create pattern rule {rule_data['rule_name']}: {e}")
    
    print(f"✅ Pattern Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_keyword_hints(created_by: UUID):
    """Create sample keyword hints"""
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
        {
            "rule_name": "Knowledge Domain - Từ khóa tiếng Việt",
            "domain": "knowledge",
            "keywords": {
                "là gì": 0.95,
                "là ai": 0.9,
                "là như thế nào": 0.9,
                "hướng dẫn": 0.85,
                "cách làm": 0.85,
                "cách": 0.8,
                "như thế nào": 0.8,
                "tại sao": 0.75,
                "vì sao": 0.75,
                "giải thích": 0.7,
                "kiến thức": 0.65,
                "thông tin": 0.65,
            },
            "description": "Từ khóa cho domain Knowledge (Kiến thức)",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for hint_data in keyword_hints:
        try:
            # Check if hint already exists to prevent duplicates
            if await rule_exists(hint_data["rule_name"], admin_config_service.list_keyword_hints):
                logger.info(f"Keyword hint already exists, skipping: {hint_data['rule_name']}")
                skipped_count += 1
                continue
            
            hint = KeywordHintCreate(**hint_data)
            await admin_config_service.create_keyword_hint(
                hint=hint,
                created_by=created_by,
            )
            created_count += 1
            logger.info(f"Created keyword hint: {hint_data['rule_name']}")
        except Exception as e:
            logger.warning(f"Failed to create keyword hint {hint_data['rule_name']}: {e}")
    
    print(f"✅ Keyword Hints - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_routing_rules(created_by: UUID):
    """Create sample routing rules"""
    from backend.schemas.admin_config_types import RoutingRuleCreate
    
    routing_rules = [
        {
            "rule_name": "HR - Tra cứu ngày phép",
            "intent_pattern": {
                "intent": "query_leave_balance",
                "match_type": "exact",
            },
            "target_domain": "hr",
            "priority": 100,
            "description": "Điều hướng câu hỏi tra cứu ngày phép đến domain HR",
        },
        {
            "rule_name": "HR - Tạo đơn nghỉ phép",
            "intent_pattern": {
                "intent": "create_leave_request",
                "match_type": "exact",
            },
            "target_domain": "hr",
            "priority": 90,
            "description": "Điều hướng yêu cầu tạo đơn nghỉ phép đến domain HR",
        },
        {
            "rule_name": "HR - Duyệt đơn nghỉ phép",
            "intent_pattern": {
                "intent": "approve_leave",
                "match_type": "exact",
            },
            "target_domain": "hr",
            "priority": 85,
            "description": "Điều hướng yêu cầu duyệt đơn nghỉ phép đến domain HR",
        },
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm",
            "intent_pattern": {
                "intent": "search_products",
                "match_type": "exact",
            },
            "target_domain": "catalog",
            "priority": 80,
            "description": "Điều hướng tìm kiếm sản phẩm đến domain Catalog",
        },
        {
            "rule_name": "Catalog - Tra cứu giá",
            "intent_pattern": {
                "intent": "query_price",
                "match_type": "exact",
            },
            "target_domain": "catalog",
            "priority": 75,
            "description": "Điều hướng tra cứu giá sản phẩm đến domain Catalog",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for rule_data in routing_rules:
        try:
            # Check if rule already exists to prevent duplicates
            if await rule_exists(rule_data["rule_name"], admin_config_service.list_routing_rules):
                logger.info(f"Routing rule already exists, skipping: {rule_data['rule_name']}")
                skipped_count += 1
                continue
            
            rule = RoutingRuleCreate(**rule_data)
            await admin_config_service.create_routing_rule(
                rule=rule,
                created_by=created_by,
            )
            created_count += 1
            logger.info(f"Created routing rule: {rule_data['rule_name']}")
        except Exception as e:
            logger.warning(f"Failed to create routing rule {rule_data['rule_name']}: {e}")
    
    print(f"✅ Routing Rules - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def create_prompt_templates(created_by: UUID):
    """Create sample prompt templates"""
    from backend.schemas.admin_config_types import PromptTemplateCreate
    
    prompt_templates = [
        {
            "rule_name": "HR - Tra cứu ngày phép System Prompt",
            "template_name": "HR - Tra cứu ngày phép System Prompt",
            "template_type": "system",
            "domain": "hr",
            "template_text": "Bạn là trợ lý nhân sự. Hãy giúp nhân viên tra cứu số ngày phép còn lại. Hãy thân thiện và chuyên nghiệp. Trả lời bằng tiếng Việt.",
            "variables": {
                "required": [],
                "optional": ["employee_name", "leave_balance"],
            },
            "description": "System prompt cho tra cứu ngày phép",
        },
        {
            "rule_name": "HR - Tạo đơn nghỉ phép System Prompt",
            "template_name": "HR - Tạo đơn nghỉ phép System Prompt",
            "template_type": "system",
            "domain": "hr",
            "template_text": "Bạn là trợ lý nhân sự. Hãy giúp nhân viên tạo đơn xin nghỉ phép. Cần thu thập thông tin: ngày bắt đầu, ngày kết thúc, và lý do nghỉ. Trả lời bằng tiếng Việt.",
            "variables": {
                "required": ["start_date", "end_date", "reason"],
                "optional": ["employee_name"],
            },
            "description": "System prompt cho tạo đơn nghỉ phép",
        },
        {
            "rule_name": "HR - Duyệt đơn nghỉ phép System Prompt",
            "template_name": "HR - Duyệt đơn nghỉ phép System Prompt",
            "template_type": "system",
            "domain": "hr",
            "template_text": "Bạn là trợ lý nhân sự. Hãy giúp quản lý duyệt đơn nghỉ phép. Chỉ quản lý và admin mới có quyền duyệt. Trả lời bằng tiếng Việt.",
            "variables": {
                "required": ["leave_request_id"],
                "optional": ["approver_name"],
            },
            "description": "System prompt cho duyệt đơn nghỉ phép",
        },
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm System Prompt",
            "template_name": "Catalog - Tìm kiếm sản phẩm System Prompt",
            "template_type": "system",
            "domain": "catalog",
            "template_text": "Bạn là trợ lý tìm kiếm sản phẩm. Hãy giúp người dùng tìm kiếm sản phẩm trong danh mục. Hỏi thêm thông tin nếu cần. Trả lời bằng tiếng Việt.",
            "variables": {
                "required": [],
                "optional": ["search_query", "category", "price_range"],
            },
            "description": "System prompt cho tìm kiếm sản phẩm",
        },
        {
            "rule_name": "Catalog - Tra cứu giá System Prompt",
            "template_name": "Catalog - Tra cứu giá System Prompt",
            "template_type": "system",
            "domain": "catalog",
            "template_text": "Bạn là trợ lý tra cứu giá. Hãy giúp người dùng tra cứu giá sản phẩm. Hiển thị giá rõ ràng và đầy đủ. Trả lời bằng tiếng Việt.",
            "variables": {
                "required": ["product_name"],
                "optional": ["product_id", "category"],
            },
            "description": "System prompt cho tra cứu giá sản phẩm",
        },
        {
            "rule_name": "Knowledge - Hỏi đáp System Prompt",
            "template_name": "Knowledge - Hỏi đáp System Prompt",
            "template_type": "system",
            "domain": "knowledge",
            "template_text": "Bạn là trợ lý hỏi đáp. Hãy trả lời câu hỏi dựa trên cơ sở kiến thức được cung cấp. Nếu không biết, hãy nói rõ. Trả lời bằng tiếng Việt.",
            "variables": {
                "required": [],
                "optional": ["context", "user_query"],
            },
            "description": "System prompt cho hỏi đáp kiến thức",
        },
        {
            "rule_name": "Meta - Chào hỏi System Prompt",
            "template_name": "Meta - Chào hỏi System Prompt",
            "template_type": "system",
            "domain": "meta",
            "template_text": "Bạn là trợ lý thân thiện. Hãy chào hỏi người dùng một cách thân thiện và nhiệt tình. Trả lời bằng tiếng Việt.",
            "variables": {
                "required": [],
                "optional": ["user_name"],
            },
            "description": "System prompt cho chào hỏi",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for template_data in prompt_templates:
        try:
            # Check if template already exists to prevent duplicates
            if await rule_exists(template_data["rule_name"], admin_config_service.list_prompt_templates):
                logger.info(f"Prompt template already exists, skipping: {template_data['rule_name']}")
                skipped_count += 1
                continue
            
            template = PromptTemplateCreate(**template_data)
            await admin_config_service.create_prompt_template(
                template=template,
                created_by=created_by,
            )
            created_count += 1
            logger.info(f"Created prompt template: {template_data['template_name']}")
        except Exception as e:
            logger.warning(f"Failed to create prompt template {template_data['template_name']}: {e}")
    
    print(f"✅ Prompt Templates - Tạo: {created_count}, Bỏ qua: {skipped_count}")


async def clean_admin_data():
    """Xóa chỉ những dữ liệu admin đã seed (không xóa data khác)"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database")
        
        # Define seeded rule names to identify which ones to delete
        seeded_pattern_rules = {
            "HR - Tra cứu số ngày phép",
            "HR - Xin nghỉ phép",
            "HR - Duyệt đơn nghỉ phép",
            "HR - Tra cứu lương",
            "Catalog - Tìm kiếm sản phẩm",
            "Catalog - Xem giá sản phẩm",
            "Chào hỏi",
            "Cảm ơn",
        }
        
        seeded_keyword_hints = {
            "HR Domain - Từ khóa tiếng Việt",
            "Catalog Domain - Từ khóa tiếng Việt",
            "Knowledge Domain - Từ khóa tiếng Việt",
        }
        
        seeded_routing_rules = {
            "HR - Tra cứu ngày phép",
            "HR - Tạo đơn nghỉ phép",
            "HR - Duyệt đơn nghỉ phép",
            "Catalog - Tìm kiếm sản phẩm",
            "Catalog - Tra cứu giá",
        }
        
        seeded_prompt_templates = {
            "HR - Tra cứu ngày phép System Prompt",
            "HR - Tạo đơn nghỉ phép System Prompt",
            "HR - Duyệt đơn nghỉ phép System Prompt",
            "Catalog - Tìm kiếm sản phẩm System Prompt",
            "Catalog - Tra cứu giá System Prompt",
            "Knowledge - Hỏi đáp System Prompt",
            "Meta - Chào hỏi System Prompt",
        }
        
        deleted_counts = {
            "pattern_rules": 0,
            "keyword_hints": 0,
            "routing_rules": 0,
            "prompt_templates": 0,
        }
        
        # 1. Delete only seeded pattern rules
        try:
            pattern_rules = await admin_config_service.list_pattern_rules(limit=1000, offset=0)
            for rule in pattern_rules.get("items", []):
                if hasattr(rule, 'rule_name') and rule.rule_name in seeded_pattern_rules:
                    try:
                        await admin_config_service.delete_pattern_rule(rule.id)
                        deleted_counts["pattern_rules"] += 1
                        logger.info(f"Deleted pattern rule: {rule.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete pattern rule {rule.id}: {e}")
        except Exception as e:
            logger.warning(f"Error listing/deleting pattern rules: {e}")
        
        # 2. Delete only seeded keyword hints
        try:
            keyword_hints = await admin_config_service.list_keyword_hints(limit=1000, offset=0)
            for hint in keyword_hints.get("items", []):
                if hasattr(hint, 'rule_name') and hint.rule_name in seeded_keyword_hints:
                    try:
                        await admin_config_service.delete_keyword_hint(hint.id)
                        deleted_counts["keyword_hints"] += 1
                        logger.info(f"Deleted keyword hint: {hint.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete keyword hint {hint.id}: {e}")
        except Exception as e:
            logger.warning(f"Error listing/deleting keyword hints: {e}")
        
        # 3. Delete only seeded routing rules
        try:
            routing_rules = await admin_config_service.list_routing_rules(limit=1000, offset=0)
            for rule in routing_rules.get("items", []):
                if hasattr(rule, 'rule_name') and rule.rule_name in seeded_routing_rules:
                    try:
                        await admin_config_service.delete_routing_rule(rule.id)
                        deleted_counts["routing_rules"] += 1
                        logger.info(f"Deleted routing rule: {rule.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete routing rule {rule.id}: {e}")
        except Exception as e:
            logger.warning(f"Error listing/deleting routing rules: {e}")
        
        # 4. Delete only seeded prompt templates
        try:
            prompt_templates = await admin_config_service.list_prompt_templates(limit=1000, offset=0)
            for template in prompt_templates.get("items", []):
                if hasattr(template, 'rule_name') and template.rule_name in seeded_prompt_templates:
                    try:
                        await admin_config_service.delete_prompt_template(template.id)
                        deleted_counts["prompt_templates"] += 1
                        logger.info(f"Deleted prompt template: {template.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete prompt template {template.id}: {e}")
        except Exception as e:
            logger.warning(f"Error listing/deleting prompt templates: {e}")
        
        # Wait a bit for cache invalidation
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully cleaned admin dashboard data")
        print("\n✅ Đã xóa dữ liệu admin dashboard thành công!")
        print("\n📝 Dữ liệu đã xóa:")
        print(f"   - Pattern rules: {deleted_counts['pattern_rules']} rules")
        print(f"   - Keyword hints: {deleted_counts['keyword_hints']} hints")
        print(f"   - Routing rules: {deleted_counts['routing_rules']} rules")
        print(f"   - Prompt templates: {deleted_counts['prompt_templates']} templates")
        
    except Exception as e:
        logger.error(f"Error cleaning admin data: {e}", exc_info=True)
        print(f"\n❌ Error cleaning data: {e}")
        raise
    finally:
        await database_client.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed or clean admin dashboard data")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean (delete) all seeded admin data instead of seeding"
    )
    args = parser.parse_args()
    
    if args.clean:
        asyncio.run(clean_admin_data())
    else:
        asyncio.run(seed_admin_data())

