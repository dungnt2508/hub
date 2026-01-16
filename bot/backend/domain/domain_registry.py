"""
Domain Registry - Pure metadata registry for domains

This registry loads domain specifications without instantiating handlers.
Handlers are only created at runtime by DomainDispatcher.

Key principles:
1. Registry only contains metadata (DomainSpec, IntentSpec)
2. No handler instantiation during registry initialization
3. STATEFUL domains (like Catalog) have no intent list
4. OPERATION domains have explicit intent specs
"""
from typing import Dict, List, Optional
from .domain_specs import (
    DomainSpec,
    IntentSpec,
    DomainType,
    InteractionMode,
    UIMode,
)
from ..shared.logger import logger


class DomainRegistry:
    """
    Registry for domain metadata.
    
    This is a pure metadata registry - no runtime coupling with handlers.
    Handlers are instantiated separately by DomainDispatcher at runtime.
    """
    
    def __init__(self):
        """Initialize registry with domain specifications"""
        self._domains: Dict[str, DomainSpec] = {}
        self._load_domain_specs()
    
    def _load_domain_specs(self):
        """Load all domain specifications"""
        try:
            # HR Domain - OPERATION domain with discrete intents
            self._domains["hr"] = DomainSpec(
                name="hr",
                display_name="Nhân sự",
                description="Quản lý nhân sự, nghỉ phép, lương",
                domain_type=DomainType.OPERATION,
                interaction_mode=InteractionMode.COMMAND,
                ui_mode=UIMode.FORM,
                intents=[
                    IntentSpec(
                        intent="create_leave_request",
                        display_name="Tạo đơn xin nghỉ phép",
                        description="Tạo đơn xin nghỉ phép mới",
                        command_type="CREATE",
                        requires_slots=True,
                        slot_names=["start_date", "end_date", "leave_type", "reason"],
                    ),
                    IntentSpec(
                        intent="query_leave_balance",
                        display_name="Tra cứu số ngày phép",
                        description="Tra cứu số ngày phép còn lại",
                        command_type="QUERY",
                        requires_slots=False,
                    ),
                    IntentSpec(
                        intent="query_leave_requests",
                        display_name="Tra cứu đơn nghỉ phép",
                        description="Tra cứu danh sách đơn nghỉ phép",
                        command_type="QUERY",
                        requires_slots=False,
                    ),
                    IntentSpec(
                        intent="approve_leave",
                        display_name="Duyệt đơn nghỉ phép",
                        description="Duyệt đơn nghỉ phép của nhân viên",
                        command_type="UPDATE",
                        requires_slots=True,
                        slot_names=["request_id", "action"],
                    ),
                    IntentSpec(
                        intent="reject_leave",
                        display_name="Từ chối đơn nghỉ phép",
                        description="Từ chối đơn nghỉ phép của nhân viên",
                        command_type="UPDATE",
                        requires_slots=True,
                        slot_names=["request_id", "reason"],
                    ),
                ],
            )
            
            # Catalog Domain - STATEFUL domain (no fixed intents)
            self._domains["catalog"] = DomainSpec(
                name="catalog",
                display_name="Danh mục sản phẩm",
                description="Tìm kiếm và tra cứu sản phẩm, mua sắm trực tuyến",
                domain_type=DomainType.STATEFUL,
                interaction_mode=InteractionMode.EXPLORE,
                ui_mode=UIMode.EXPLORE,
                intents=[],  # STATEFUL domains have no fixed intent list
                metadata={
                    "stateful": True,
                    "uses_intent_registry": True,  # Catalog uses intent_registry.yaml for dynamic mapping
                },
            )
            
            # DBA Domain - OPERATION domain with discrete intents
            self._domains["dba"] = DomainSpec(
                name="dba",
                display_name="Quản trị cơ sở dữ liệu",
                description="Phân tích hiệu năng, tối ưu, giám sát cơ sở dữ liệu",
                domain_type=DomainType.OPERATION,
                interaction_mode=InteractionMode.COMMAND,
                ui_mode=UIMode.DASHBOARD,
                intents=[
                    IntentSpec(
                        intent="validate_custom_sql",
                        display_name="Kiểm tra SQL queries",
                        description="Kiểm tra và validate SQL queries tùy chỉnh",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["sql_query", "database_name"],
                    ),
                    IntentSpec(
                        intent="compare_sp_blitz_vs_custom",
                        display_name="So sánh sp_Blitz vs Custom",
                        description="So sánh kết quả giữa sp_Blitz và custom queries",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["query_type", "database_name"],
                    ),
                    IntentSpec(
                        intent="incident_triage",
                        display_name="Phân loại và phân tích incidents",
                        description="Phân loại và phân tích database incidents",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["incident_id", "severity"],
                    ),
                    IntentSpec(
                        intent="store_query_metrics",
                        display_name="Lưu trữ metrics query",
                        description="Lưu trữ metrics từ query execution",
                        command_type="CREATE",
                        requires_slots=True,
                        slot_names=["query_id", "metrics"],
                    ),
                    IntentSpec(
                        intent="get_active_alerts",
                        display_name="Lấy danh sách alerts đang hoạt động",
                        description="Lấy danh sách các alerts đang hoạt động trong database",
                        command_type="QUERY",
                        requires_slots=False,
                    ),
                    IntentSpec(
                        intent="analyze_slow_query",
                        display_name="Phân tích slow query",
                        description="Phân tích các query chạy chậm",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["query_id", "database_name"],
                    ),
                    IntentSpec(
                        intent="check_index_health",
                        display_name="Kiểm tra sức khỏe index",
                        description="Kiểm tra tình trạng sức khỏe của các index",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["database_name", "table_name"],
                    ),
                    IntentSpec(
                        intent="detect_blocking",
                        display_name="Phát hiện blocking",
                        description="Phát hiện các blocking queries",
                        command_type="QUERY",
                        requires_slots=False,
                    ),
                    IntentSpec(
                        intent="analyze_wait_stats",
                        display_name="Phân tích wait stats",
                        description="Phân tích wait statistics của database",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["database_name"],
                    ),
                    IntentSpec(
                        intent="analyze_query_regression",
                        display_name="Phân tích query regression",
                        description="Phân tích sự suy giảm hiệu năng của queries",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["query_id", "time_range"],
                    ),
                    IntentSpec(
                        intent="detect_deadlock_pattern",
                        display_name="Phát hiện deadlock pattern",
                        description="Phát hiện các pattern gây deadlock",
                        command_type="QUERY",
                        requires_slots=False,
                    ),
                    IntentSpec(
                        intent="analyze_io_pressure",
                        display_name="Phân tích I/O pressure",
                        description="Phân tích áp lực I/O của database",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["database_name"],
                    ),
                    IntentSpec(
                        intent="capacity_forecast",
                        display_name="Dự báo dung lượng",
                        description="Dự báo dung lượng database trong tương lai",
                        command_type="QUERY",
                        requires_slots=True,
                        slot_names=["database_name", "forecast_period"],
                    ),
                ],
            )
            
            # Knowledge Domain - KNOWLEDGE domain
            self._domains["knowledge"] = DomainSpec(
                name="knowledge",
                display_name="Kiến thức",
                description="Hỏi đáp dựa trên knowledge base",
                domain_type=DomainType.KNOWLEDGE,
                interaction_mode=InteractionMode.QUERY,
                ui_mode=UIMode.CHAT,
                intents=[],  # KNOWLEDGE domains handle queries dynamically
                metadata={
                    "uses_rag": True,
                },
            )
            
            # Meta Domain - META domain
            self._domains["meta"] = DomainSpec(
                name="meta",
                display_name="Meta",
                description="Các tác vụ meta như chào hỏi, cảm ơn",
                domain_type=DomainType.META,
                interaction_mode=InteractionMode.CONVERSATIONAL,
                ui_mode=UIMode.CHAT,
                intents=[],  # META domains handle tasks dynamically
            )
            
            logger.info(
                f"Domain registry initialized with {len(self._domains)} domains",
                extra={
                    "domains": list(self._domains.keys()),
                    "operation_domains": [
                        name for name, spec in self._domains.items()
                        if spec.domain_type == DomainType.OPERATION
                    ],
                    "stateful_domains": [
                        name for name, spec in self._domains.items()
                        if spec.domain_type == DomainType.STATEFUL
                    ],
                }
            )
            
        except Exception as e:
            logger.error(f"Error loading domain specs: {e}", exc_info=True)
            raise
    
    def get_domain(self, domain_name: str) -> Optional[DomainSpec]:
        """Get domain specification by name"""
        return self._domains.get(domain_name)
    
    def get_all_domains(self) -> List[DomainSpec]:
        """Get all domain specifications"""
        return list(self._domains.values())
    
    def get_domains_by_type(self, domain_type: DomainType) -> List[DomainSpec]:
        """Get domains by type"""
        return [
            spec for spec in self._domains.values()
            if spec.domain_type == domain_type
        ]
    
    def get_all_intents(self) -> List[Dict[str, Any]]:
        """
        Get all intents across OPERATION domains only.
        
        STATEFUL, KNOWLEDGE, and META domains do not have fixed intents.
        """
        intents = []
        for domain_spec in self._domains.values():
            if domain_spec.has_intents():
                for intent_spec in domain_spec.intents:
                    intents.append({
                        "intent": intent_spec.intent,
                        "display_name": intent_spec.display_name,
                        "description": intent_spec.description,
                        "command_type": intent_spec.command_type,
                        "requires_slots": intent_spec.requires_slots,
                        "slot_names": intent_spec.slot_names,
                        "domain": domain_spec.name,
                        "domain_display_name": domain_spec.display_name,
                        "domain_type": domain_spec.domain_type.value,
                        "interaction_mode": domain_spec.interaction_mode.value,
                        "ui_mode": domain_spec.ui_mode.value,
                        "metadata": intent_spec.metadata,
                    })
        return intents
    
    def get_intents_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        """
        Get intents for specific domain.
        
        Returns empty list for STATEFUL, KNOWLEDGE, or META domains.
        """
        domain_spec = self._domains.get(domain_name)
        if not domain_spec or not domain_spec.has_intents():
            return []
        
        return [
            {
                "intent": intent_spec.intent,
                "display_name": intent_spec.display_name,
                "description": intent_spec.description,
                "command_type": intent_spec.command_type,
                "requires_slots": intent_spec.requires_slots,
                "slot_names": intent_spec.slot_names,
                "metadata": intent_spec.metadata,
            }
            for intent_spec in domain_spec.intents
        ]
    
    def domain_exists(self, domain_name: str) -> bool:
        """Check if domain exists in registry"""
        return domain_name in self._domains
    
    def is_operation_domain(self, domain_name: str) -> bool:
        """Check if domain is OPERATION type"""
        domain_spec = self._domains.get(domain_name)
        return domain_spec is not None and domain_spec.domain_type == DomainType.OPERATION
    
    def is_stateful_domain(self, domain_name: str) -> bool:
        """Check if domain is STATEFUL type"""
        domain_spec = self._domains.get(domain_name)
        return domain_spec is not None and domain_spec.domain_type == DomainType.STATEFUL


# Global registry instance
domain_registry = DomainRegistry()
