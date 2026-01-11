"""
Seed DBA Domain Routing Data
Tạo sample routing data cho DBA domain

Usage:
    # Seed data
    python -m backend.scripts.seed_dba_routing_data
    
    # Clean (delete) all seeded data
    python -m backend.scripts.seed_dba_routing_data --clean
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


async def seed_dba_data():
    """Seed DBA domain with routing data"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database")
        
        # Get admin user ID
        admin_service = AdminUserService()
        admin_user = await admin_service.get_admin_user_by_email("gsnake1102@gmail.com")
        admin_user_id = UUID(str(admin_user["id"]))
        
        # Create DBA routing data
        await create_dba_pattern_rules(admin_user_id)
        await create_dba_keyword_hints(admin_user_id)
        await create_dba_routing_rules(admin_user_id)
        await create_dba_prompt_templates(admin_user_id)
        
        # Wait for cache invalidation
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully seeded DBA domain routing data")
        print("\n✅ Đã tạo dữ liệu routing cho DBA domain thành công!")
        print("\n📝 Dữ liệu đã tạo:")
        print("   - Pattern rules: 11 rules (DBA use cases)")
        print("   - Keyword hints: 2 keywords (database, performance)")
        print("   - Routing rules: 11 rules (map to DBA intents)")
        print("   - Prompt templates: 4 templates (DBA prompts)")
        
    except Exception as e:
        logger.error(f"Error seeding DBA data: {e}", exc_info=True)
        print(f"\n❌ Error seeding DBA data: {e}")
        raise
    finally:
        await database_client.disconnect()


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


async def create_dba_pattern_rules(created_by: UUID):
    """Create pattern rules for DBA use cases"""
    from backend.schemas.admin_config_types import PatternRuleCreate
    
    pattern_rules = [
        {
            "rule_name": "DBA - Phân tích query chạy chậm",
            "pattern_regex": r"(?:tìm|find|list|liệt kê|xem|view).*(?:query|queries|sql).*(?:chậm|slow|chạy chậm|slow query|performance)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "analyze_slow_query",
            "intent_type": "OPERATION",
            "priority": 95,
            "description": "Phân tích query chạy chậm",
        },
        {
            "rule_name": "DBA - Phân tích query chạy chậm (alt)",
            "pattern_regex": r"(?:query|queries|sql).*(?:chậm|slow|performance|hiệu năng).*(?:analysis|phân tích|tìm|find|detection|phát hiện)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "analyze_slow_query",
            "intent_type": "OPERATION",
            "priority": 93,
            "description": "Phân tích query chạy chậm (alternative pattern)",
        },
        {
            "rule_name": "DBA - Kiểm tra sức khỏe index",
            "pattern_regex": r"(?:index|index health|sức khỏe|khỏe mạnh|index status|fragmentation)\s+(?:check|kiểm tra|tình trạng|như thế nào)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "check_index_health",
            "intent_type": "OPERATION",
            "priority": 90,
            "description": "Kiểm tra sức khỏe index",
        },
        {
            "rule_name": "DBA - Phát hiện blocking",
            "pattern_regex": r"(?:blocking|block|bị khoá|lock|khóa|chặn)\s+(?:detect|phát hiện|session|sessions)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "detect_blocking",
            "intent_type": "OPERATION",
            "priority": 90,
            "description": "Phát hiện blocking sessions",
        },
        {
            "rule_name": "DBA - Phân tích wait stats",
            "pattern_regex": r"(?:wait|chờ|đợi|stats|statistics|event)\s+(?:analysis|phân tích)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "analyze_wait_stats",
            "intent_type": "OPERATION",
            "priority": 85,
            "description": "Phân tích wait statistics",
        },
        {
            "rule_name": "DBA - Phát hiện query regression",
            "pattern_regex": r"(?:regression|performance|degradation|giảm|tệ hơn)\s+(?:query|detect|phát hiện)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "analyze_query_regression",
            "intent_type": "OPERATION",
            "priority": 85,
            "description": "Phát hiện performance regression",
        },
        {
            "rule_name": "DBA - Phát hiện deadlock",
            "pattern_regex": r"(?:deadlock|deadlock pattern|deadlock detection)\s+(?:detect|phát hiện|pattern)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "detect_deadlock_pattern",
            "intent_type": "OPERATION",
            "priority": 85,
            "description": "Phát hiện deadlock patterns",
        },
        {
            "rule_name": "DBA - Phân tích I/O pressure",
            "pattern_regex": r"(?:io|i/o|input|output|pressure|disk|đĩa)\s+(?:analysis|phân tích|pressure)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "analyze_io_pressure",
            "intent_type": "OPERATION",
            "priority": 80,
            "description": "Phân tích I/O pressure",
        },
        {
            "rule_name": "DBA - Dự báo capacity",
            "pattern_regex": r"(?:capacity|capacity forecast|dự báo|forecast|storage|dung lượng)\s+(?:forecast|dự báo|planning)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "capacity_forecast",
            "intent_type": "OPERATION",
            "priority": 80,
            "description": "Dự báo capacity",
        },
        {
            "rule_name": "DBA - Validate custom SQL",
            "pattern_regex": r"(?:validate|kiểm tra|check)\s+(?:sql|query|custom|statement)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "validate_custom_sql",
            "intent_type": "OPERATION",
            "priority": 75,
            "description": "Validate SQL queries",
        },
        {
            "rule_name": "DBA - So sánh sp_Blitz vs Custom",
            "pattern_regex": r"(?:blitz|sp_blitz|compare|so sánh|comparison)\s+(?:custom|analysis)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "compare_sp_blitz_vs_custom",
            "intent_type": "OPERATION",
            "priority": 70,
            "description": "So sánh sp_Blitz vs custom analysis",
        },
        {
            "rule_name": "DBA - Phân loại incident",
            "pattern_regex": r"(?:incident|sự cố|vấn đề|lỗi|problem)\s+(?:triage|phân loại|analyze|phân tích)",
            "pattern_flags": "IGNORECASE",
            "target_domain": "dba",
            "target_intent": "incident_triage",
            "intent_type": "OPERATION",
            "priority": 85,
            "description": "Phân loại và phân tích database incidents",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for rule_data in pattern_rules:
        try:
            # Check if rule already exists
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


async def create_dba_keyword_hints(created_by: UUID):
    """Create keyword hints for DBA domain"""
    from backend.schemas.admin_config_types import KeywordHintCreate
    
    keyword_hints = [
        {
            "rule_name": "DBA Domain - Từ khóa Performance",
            "domain": "dba",
            "keywords": {
                "performance": 0.95,
                "query": 0.95,
                "database": 0.9,
                "index": 0.9,
                "slow": 0.85,
                "optimization": 0.85,
                "tối ưu": 0.85,
                "hiệu năng": 0.85,
                "query chậm": 0.8,
                "chậm": 0.8,
                "blocking": 0.85,
                "deadlock": 0.85,
                "lock": 0.8,
                "khóa": 0.8,
                "capacity": 0.8,
                "dung lượng": 0.8,
            },
            "description": "Từ khóa cho domain DBA (Database Administration)",
        },
        {
            "rule_name": "DBA Domain - Từ khóa Analysis",
            "domain": "dba",
            "keywords": {
                "phân tích": 0.95,
                "analysis": 0.95,
                "incident": 0.9,
                "sự cố": 0.9,
                "triage": 0.85,
                "phân loại": 0.85,
                "forecast": 0.8,
                "dự báo": 0.8,
                "validation": 0.8,
                "validate": 0.8,
                "kiểm tra": 0.8,
                "health": 0.75,
                "sức khỏe": 0.75,
                "regression": 0.75,
                "degradation": 0.75,
            },
            "description": "Từ khóa cho phân tích DBA",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for hint_data in keyword_hints:
        try:
            # Check if hint already exists
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


async def create_dba_routing_rules(created_by: UUID):
    """Create routing rules for DBA intents"""
    from backend.schemas.admin_config_types import RoutingRuleCreate
    
    routing_rules = [
        {
            "rule_name": "DBA - Analyze Slow Query",
            "intent_pattern": {
                "intent": "analyze_slow_query",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 95,
            "description": "Route slow query analysis requests to DBA domain",
        },
        {
            "rule_name": "DBA - Check Index Health",
            "intent_pattern": {
                "intent": "check_index_health",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 90,
            "description": "Route index health checks to DBA domain",
        },
        {
            "rule_name": "DBA - Detect Blocking",
            "intent_pattern": {
                "intent": "detect_blocking",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 90,
            "description": "Route blocking detection to DBA domain",
        },
        {
            "rule_name": "DBA - Analyze Wait Stats",
            "intent_pattern": {
                "intent": "analyze_wait_stats",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 85,
            "description": "Route wait stats analysis to DBA domain",
        },
        {
            "rule_name": "DBA - Query Regression Analysis",
            "intent_pattern": {
                "intent": "analyze_query_regression",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 85,
            "description": "Route query regression analysis to DBA domain",
        },
        {
            "rule_name": "DBA - Detect Deadlock Pattern",
            "intent_pattern": {
                "intent": "detect_deadlock_pattern",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 85,
            "description": "Route deadlock detection to DBA domain",
        },
        {
            "rule_name": "DBA - Analyze I/O Pressure",
            "intent_pattern": {
                "intent": "analyze_io_pressure",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 80,
            "description": "Route I/O pressure analysis to DBA domain",
        },
        {
            "rule_name": "DBA - Capacity Forecast",
            "intent_pattern": {
                "intent": "capacity_forecast",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 80,
            "description": "Route capacity forecasting to DBA domain",
        },
        {
            "rule_name": "DBA - Validate Custom SQL",
            "intent_pattern": {
                "intent": "validate_custom_sql",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 75,
            "description": "Route SQL validation to DBA domain",
        },
        {
            "rule_name": "DBA - Compare sp_Blitz vs Custom",
            "intent_pattern": {
                "intent": "compare_sp_blitz_vs_custom",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 70,
            "description": "Route sp_Blitz comparison to DBA domain",
        },
        {
            "rule_name": "DBA - Incident Triage",
            "intent_pattern": {
                "intent": "incident_triage",
                "match_type": "exact",
            },
            "target_domain": "dba",
            "priority": 85,
            "description": "Route incident triage to DBA domain",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for rule_data in routing_rules:
        try:
            # Check if rule already exists
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


async def create_dba_prompt_templates(created_by: UUID):
    """Create system prompt templates for DBA domain"""
    from backend.schemas.admin_config_types import PromptTemplateCreate
    
    prompt_templates = [
        {
            "rule_name": "DBA - Performance Analysis System Prompt",
            "template_name": "DBA - Performance Analysis System Prompt",
            "template_type": "system",
            "domain": "dba",
            "template_text": "Bạn là trợ lý DBA (Database Administrator) chuyên phân tích hiệu năng cơ sở dữ liệu. "
                           "Hãy giúp người dùng phân tích và tối ưu performance database. "
                           "Cung cấp các khuyến nghị chi tiết về queries, indexes, và configuration. "
                           "Trả lời bằng tiếng Việt và cung cấp đầy đủ giải thích.",
            "variables": {
                "required": [],
                "optional": ["database_type", "issue_type", "specific_query"],
            },
            "description": "System prompt cho phân tích performance database",
        },
        {
            "rule_name": "DBA - Query Optimization System Prompt",
            "template_name": "DBA - Query Optimization System Prompt",
            "template_type": "system",
            "domain": "dba",
            "template_text": "Bạn là trợ lý DBA chuyên về tối ưu queries. "
                           "Giúp người dùng phân tích execution plans, suggest indexes, và optimize queries. "
                           "Giải thích chi tiết về từng bước optimize và tác động đến performance. "
                           "Trả lời bằng tiếng Việt với các ví dụ cụ thể.",
            "variables": {
                "required": [],
                "optional": ["query_text", "database_type", "current_performance"],
            },
            "description": "System prompt cho tối ưu queries",
        },
        {
            "rule_name": "DBA - Incident Resolution System Prompt",
            "template_name": "DBA - Incident Resolution System Prompt",
            "template_type": "system",
            "domain": "dba",
            "template_text": "Bạn là trợ lý DBA chuyên xử lý database incidents. "
                           "Giúp người dùng phân loại, phân tích và giải quyết các sự cố database như: "
                           "slow queries, blocking, deadlocks, capacity issues. "
                           "Cung cấp immediate actions và long-term solutions. "
                           "Trả lời bằng tiếng Việt với chi tiết và cấp độ ưu tiên.",
            "variables": {
                "required": [],
                "optional": ["incident_type", "symptoms", "affected_queries"],
            },
            "description": "System prompt cho xử lý database incidents",
        },
        {
            "rule_name": "DBA - Capacity Planning System Prompt",
            "template_name": "DBA - Capacity Planning System Prompt",
            "template_type": "system",
            "domain": "dba",
            "template_text": "Bạn là trợ lý DBA chuyên về capacity planning. "
                           "Giúp người dùng dự báo growth, lập kế hoạch scaling, và quản lý resources. "
                           "Cung cấp thông tin về disk space, memory, connections, và recommendations. "
                           "Trả lời bằng tiếng Việt với số liệu cụ thể và timeline.",
            "variables": {
                "required": [],
                "optional": ["current_usage", "growth_rate", "forecast_period"],
            },
            "description": "System prompt cho capacity planning",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for template_data in prompt_templates:
        try:
            # Check if template already exists
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


async def clean_dba_data():
    """Delete all seeded DBA routing data"""
    try:
        # Connect to database
        await database_client.connect()
        logger.info("Connected to database")
        
        deleted_counts = {
            "pattern_rules": 0,
            "keyword_hints": 0,
            "routing_rules": 0,
            "prompt_templates": 0,
        }
        
        # 1. Delete DBA pattern rules
        try:
            pattern_rules = await admin_config_service.list_pattern_rules(limit=1000, offset=0)
            for rule in pattern_rules.get("items", []):
                if hasattr(rule, 'target_domain') and rule.target_domain == "dba":
                    try:
                        await admin_config_service.delete_pattern_rule(rule.id)
                        deleted_counts["pattern_rules"] += 1
                        logger.info(f"Deleted DBA pattern rule: {rule.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete pattern rule {rule.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting pattern rules: {e}")
        
        # 2. Delete DBA keyword hints
        try:
            keyword_hints = await admin_config_service.list_keyword_hints(limit=1000, offset=0)
            for hint in keyword_hints.get("items", []):
                if hasattr(hint, 'domain') and hint.domain == "dba":
                    try:
                        await admin_config_service.delete_keyword_hint(hint.id)
                        deleted_counts["keyword_hints"] += 1
                        logger.info(f"Deleted DBA keyword hint: {hint.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete keyword hint {hint.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting keyword hints: {e}")
        
        # 3. Delete DBA routing rules
        try:
            routing_rules = await admin_config_service.list_routing_rules(limit=1000, offset=0)
            for rule in routing_rules.get("items", []):
                if hasattr(rule, 'target_domain') and rule.target_domain == "dba":
                    try:
                        await admin_config_service.delete_routing_rule(rule.id)
                        deleted_counts["routing_rules"] += 1
                        logger.info(f"Deleted DBA routing rule: {rule.rule_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete routing rule {rule.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting routing rules: {e}")
        
        # 4. Delete DBA prompt templates
        try:
            prompt_templates = await admin_config_service.list_prompt_templates(limit=1000, offset=0)
            for template in prompt_templates.get("items", []):
                if hasattr(template, 'domain') and template.domain == "dba":
                    try:
                        await admin_config_service.delete_prompt_template(template.id)
                        deleted_counts["prompt_templates"] += 1
                        logger.info(f"Deleted DBA prompt template: {template.template_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete prompt template {template.id}: {e}")
        except Exception as e:
            logger.warning(f"Error deleting prompt templates: {e}")
        
        # Wait for cache invalidation
        await asyncio.sleep(1)
        
        logger.info("✅ Successfully cleaned DBA routing data")
        print("\n✅ Đã xóa dữ liệu DBA routing thành công!")
        print("\n📝 Dữ liệu đã xóa:")
        print(f"   - Pattern rules: {deleted_counts['pattern_rules']} rules")
        print(f"   - Keyword hints: {deleted_counts['keyword_hints']} hints")
        print(f"   - Routing rules: {deleted_counts['routing_rules']} rules")
        print(f"   - Prompt templates: {deleted_counts['prompt_templates']} templates")
        
    except Exception as e:
        logger.error(f"Error cleaning DBA data: {e}", exc_info=True)
        print(f"\n❌ Error cleaning DBA data: {e}")
        raise
    finally:
        await database_client.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed or clean DBA domain routing data")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean (delete) all seeded DBA routing data instead of seeding"
    )
    args = parser.parse_args()
    
    if args.clean:
        asyncio.run(clean_dba_data())
    else:
        asyncio.run(seed_dba_data())
