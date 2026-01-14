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
        # =========================
        # SEARCH / DISCOVERY
        # =========================
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm chung",
            "pattern_regex": r"(tìm|tìm kiếm|có|bán|mua|xem)\s+(sản phẩm|hàng|đồ|món|sp)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "search_products",
            "intent_type": "KNOWLEDGE",
            "priority": 80,
            "description": "Người dùng muốn xem hoặc tìm sản phẩm trong catalog",
        },
        {
            "rule_name": "Catalog - Tìm sản phẩm theo loại/category",
            "pattern_regex": r"(tìm|xem|có)\s+(.*)\s+(không|ko|không?)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "search_by_category",
            "intent_type": "KNOWLEDGE",
            "priority": 75,
            "description": "Tìm sản phẩm theo category hoặc loại cụ thể",
        },

        # =========================
        # PRICE
        # =========================
        {
            "rule_name": "Catalog - Hỏi giá sản phẩm",
            "pattern_regex": r"(giá|bao nhiêu tiền|bao nhiêu|giá cả)\s*(của)?\s*(sản phẩm|món|hàng|sp)?",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "query_price",
            "intent_type": "KNOWLEDGE",
            "priority": 90,
            "description": "Tra cứu giá sản phẩm",
        },

        # =========================
        # PRODUCT DETAIL
        # =========================
        {
            "rule_name": "Catalog - Xem thông tin chi tiết sản phẩm",
            "pattern_regex": r"(thông tin|chi tiết|mô tả|spec|cấu hình)\s+(sản phẩm|món|hàng|sp)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "query_product_detail",
            "intent_type": "KNOWLEDGE",
            "priority": 85,
            "description": "Xem thông tin chi tiết của sản phẩm",
        },

        # =========================
        # AVAILABILITY
        # =========================
        {
            "rule_name": "Catalog - Kiểm tra còn hàng",
            "pattern_regex": r"(còn hàng|hết hàng|có sẵn|available|in stock)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "check_availability",
            "intent_type": "KNOWLEDGE",
            "priority": 95,
            "description": "Kiểm tra tình trạng còn hàng",
        },

        # =========================
        # VARIANT / ATTRIBUTE
        # =========================
        {
            "rule_name": "Catalog - Hỏi biến thể sản phẩm",
            "pattern_regex": r"(size|màu|màu sắc|phiên bản|variant|loại nào)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "query_variant",
            "intent_type": "KNOWLEDGE",
            "priority": 70,
            "description": "Hỏi các biến thể hoặc thuộc tính sản phẩm",
        },

        # =========================
        # COMPARISON
        # =========================
        {
            "rule_name": "Catalog - So sánh sản phẩm",
            "pattern_regex": r"(so sánh|khác gì|hơn gì|so với)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "catalog",
            "target_intent": "compare_products",
            "intent_type": "KNOWLEDGE",
            "priority": 60,
            "description": "So sánh hai hoặc nhiều sản phẩm",
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
            "rule_name": "Catalog Domain - Vietnamese Keywords (Normalized)",
            "domain": "catalog",
            "keywords": {
                # CORE OBJECT
                "sản phẩm": 0.98,
                "product": 0.95,
                "sp": 0.95,
                "hàng hóa": 0.92,
                "mặt hàng": 0.92,

                # CATEGORY / STRUCTURE
                "danh mục": 0.9,
                "loại": 0.85,
                "category": 0.85,
                "catalog": 0.85,

                # SEARCH / DISCOVERY
                "tìm": 0.8,
                "tìm kiếm": 0.8,
                "xem": 0.75,
                "có bán": 0.85,
                "có hàng": 0.85,

                # PRICE
                "giá": 0.9,
                "bao nhiêu tiền": 0.95,
                "giá bao nhiêu": 0.95,
                "giá cả": 0.85,
                "giá tiền": 0.85,

                # DETAIL / INFO
                "thông tin": 0.85,
                "chi tiết": 0.85,
                "mô tả": 0.8,
                "spec": 0.8,
                "cấu hình": 0.8,

                # VARIANT / ATTRIBUTE
                "size": 0.8,
                "màu": 0.8,
                "màu sắc": 0.8,
                "phiên bản": 0.8,
                "variant": 0.8,

                # AVAILABILITY
                "còn hàng": 0.95,
                "hết hàng": 0.95,
                "available": 0.9,
                "in stock": 0.9,

                # COMPARISON
                "so sánh": 0.75,
                "so với": 0.75,
                "khác gì": 0.75,
            },
            "description": "Keyword hints chuẩn hóa cho domain Catalog, tối ưu routing intent truy vấn sản phẩm",
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
        # =========================
        # HARD ROUTE – HIGH CONFIDENCE
        # =========================
        {
            "rule_name": "Catalog - Kiểm tra tồn kho",
            "intent_pattern": {"intent": "check_availability", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 95,
            "description": "Routing intent kiểm tra còn hàng vào catalog domain",
        },
        {
            "rule_name": "Catalog - Tra cứu giá sản phẩm",
            "intent_pattern": {"intent": "query_price", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 92,
            "description": "Routing intent hỏi giá vào catalog domain",
        },

        # =========================
        # PRODUCT DETAIL
        # =========================
        {
            "rule_name": "Catalog - Xem chi tiết sản phẩm",
            "intent_pattern": {"intent": "query_product_detail", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 90,
            "description": "Routing intent xem thông tin chi tiết sản phẩm",
        },
        {
            "rule_name": "Catalog - Hỏi biến thể sản phẩm",
            "intent_pattern": {"intent": "query_variant", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 85,
            "description": "Routing intent hỏi size, màu, phiên bản sản phẩm",
        },

        # =========================
        # SEARCH / DISCOVERY
        # =========================
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm chung",
            "intent_pattern": {"intent": "search_products", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 80,
            "description": "Routing intent tìm kiếm sản phẩm vào catalog domain",
        },
        {
            "rule_name": "Catalog - Tìm theo danh mục",
            "intent_pattern": {"intent": "search_by_category", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 78,
            "description": "Routing intent tìm sản phẩm theo danh mục",
        },

        # =========================
        # COMPARISON
        # =========================
        {
            "rule_name": "Catalog - So sánh sản phẩm",
            "intent_pattern": {"intent": "compare_products", "match_type": "exact"},
            "target_domain": "catalog",
            "priority": 70,
            "description": "Routing intent so sánh sản phẩm",
        },

        # =========================
        # FALLBACK GUARD
        # =========================
        {
            "rule_name": "Catalog - Fallback Knowledge",
            "intent_pattern": {"intent": "catalog_knowledge", "match_type": "prefix"},
            "target_domain": "catalog",
            "priority": 60,
            "description": "Fallback cho các intent knowledge liên quan catalog nhưng chưa phân loại rõ",
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
        # =========================
        # SEARCH
        # =========================
        {
            "rule_name": "Catalog - Tìm kiếm sản phẩm (System)",
            "template_name": "catalog_search_system",
            "template_type": "system",
            "domain": "catalog",
            "template_text": (
                "Bạn là catalog search engine. "
                "Nhiệm vụ: trả về danh sách sản phẩm khớp điều kiện tìm kiếm từ catalog. "
                "Chỉ sử dụng dữ liệu catalog được cung cấp. "
                "Không suy đoán. Không hỏi thêm. "
                "Nếu không có kết quả, trả lời rõ: không tìm thấy sản phẩm phù hợp. "
                "Output ngắn gọn, liệt kê theo danh sách. "
                "Ngôn ngữ: tiếng Việt."
            ),
            "variables": {
                "required": ["search_query"],
                "optional": ["category", "price_range", "attributes"]
            },
            "description": "System prompt cho use case tìm kiếm sản phẩm trong catalog",
        },

        # =========================
        # PRICE
        # =========================
        {
            "rule_name": "Catalog - Tra cứu giá sản phẩm (System)",
            "template_name": "catalog_price_query_system",
            "template_type": "system",
            "domain": "catalog",
            "template_text": (
                "Bạn là catalog pricing engine. "
                "Nhiệm vụ: trả về giá chính xác của sản phẩm từ catalog. "
                "Không giải thích. Không marketing. "
                "Nếu thiếu giá hoặc sản phẩm không tồn tại, nói rõ thiếu dữ liệu nào. "
                "Giá phải hiển thị rõ ràng, đúng đơn vị. "
                "Ngôn ngữ: tiếng Việt."
            ),
            "variables": {
                "required": ["product_name"],
                "optional": ["product_id", "variant_id"]
            },
            "description": "System prompt cho tra cứu giá sản phẩm",
        },

        # =========================
        # PRODUCT DETAIL
        # =========================
        {
            "rule_name": "Catalog - Thông tin chi tiết sản phẩm (System)",
            "template_name": "catalog_product_detail_system",
            "template_type": "system",
            "domain": "catalog",
            "template_text": (
                "Bạn là catalog product information engine. "
                "Nhiệm vụ: trả về thông tin chi tiết sản phẩm từ catalog. "
                "Bao gồm: mô tả, thuộc tính, biến thể nếu có. "
                "Không suy diễn công dụng. "
                "Nếu field nào không có trong dữ liệu, ghi rõ là không có. "
                "Ngôn ngữ: tiếng Việt."
            ),
            "variables": {
                "required": ["product_name"],
                "optional": ["product_id"]
            },
            "description": "System prompt cho truy vấn thông tin chi tiết sản phẩm",
        },

        # =========================
        # AVAILABILITY
        # =========================
        {
            "rule_name": "Catalog - Kiểm tra tồn kho (System)",
            "template_name": "catalog_availability_system",
            "template_type": "system",
            "domain": "catalog",
            "template_text": (
                "Bạn là catalog availability engine. "
                "Nhiệm vụ: trả về trạng thái còn hàng của sản phẩm. "
                "Chỉ trả lời: còn hàng / hết hàng / không có dữ liệu. "
                "Không đưa khuyến nghị mua. "
                "Ngôn ngữ: tiếng Việt."
            ),
            "variables": {
                "required": ["product_name"],
                "optional": ["variant_id"]
            },
            "description": "System prompt cho kiểm tra tình trạng tồn kho",
        },

        # =========================
        # COMPARISON
        # =========================
        {
            "rule_name": "Catalog - So sánh sản phẩm (System)",
            "template_name": "catalog_product_comparison_system",
            "template_type": "system",
            "domain": "catalog",
            "template_text": (
                "Bạn là catalog comparison engine. "
                "Nhiệm vụ: so sánh các sản phẩm dựa trên dữ liệu catalog. "
                "Chỉ so sánh các field tồn tại. "
                "Không đánh giá chủ quan. "
                "Output dạng bảng hoặc bullet rõ ràng. "
                "Ngôn ngữ: tiếng Việt."
            ),
            "variables": {
                "required": ["products"],
                "optional": ["compare_fields"]
            },
            "description": "System prompt cho so sánh sản phẩm",
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
