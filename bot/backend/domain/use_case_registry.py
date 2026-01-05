"""
Use Case Registry - Discover and register available use cases
"""
from typing import Dict, List, Any
from .hr.entry_handler import HREntryHandler
from .catalog.entry_handler import CatalogEntryHandler
from ..shared.logger import logger


class UseCaseRegistry:
    """
    Registry for discovering available use cases across all domains.
    
    This helps frontend show available intents and domains.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._domains: Dict[str, Dict[str, Any]] = {}
            self._initialized = True
            self._discover_use_cases()
    
    def _discover_use_cases(self):
        """Discover use cases from all domain handlers"""
        try:
            # HR Domain
            hr_handler = HREntryHandler()
            hr_intents = list(hr_handler.use_cases.keys())
            
            self._domains["hr"] = {
                "name": "HR",
                "display_name": "Nhân sự",
                "description": "Quản lý nhân sự, nghỉ phép, lương",
                "intents": [
                    {
                        "intent": intent,
                        "display_name": self._format_intent_name(intent),
                        "description": self._get_intent_description("hr", intent),
                        "intent_type": "OPERATION",
                    }
                    for intent in hr_intents
                ],
                "intent_type": "OPERATION",
            }
            
            # Catalog Domain
            # Catalog handles KNOWLEDGE intents dynamically
            self._domains["catalog"] = {
                "name": "catalog",
                "display_name": "Danh mục sản phẩm",
                "description": "Tìm kiếm và tra cứu sản phẩm",
                "intents": [
                    {
                        "intent": "search_products",
                        "display_name": "Tìm kiếm sản phẩm",
                        "description": "Tìm kiếm sản phẩm trong catalog",
                        "intent_type": "KNOWLEDGE",
                    },
                    {
                        "intent": "query_price",
                        "display_name": "Tra cứu giá",
                        "description": "Tra cứu giá sản phẩm",
                        "intent_type": "KNOWLEDGE",
                    },
                ],
                "intent_type": "KNOWLEDGE",
            }
            
            # Knowledge Domain
            self._domains["knowledge"] = {
                "name": "knowledge",
                "display_name": "Kiến thức",
                "description": "Hỏi đáp dựa trên knowledge base",
                "intents": [
                    {
                        "intent": "ask_question",
                        "display_name": "Hỏi đáp",
                        "description": "Trả lời câu hỏi dựa trên knowledge base",
                        "intent_type": "KNOWLEDGE",
                    },
                ],
                "intent_type": "KNOWLEDGE",
            }
            
            # Meta Domain
            self._domains["meta"] = {
                "name": "meta",
                "display_name": "Meta",
                "description": "Các tác vụ meta như chào hỏi, cảm ơn",
                "intents": [
                    {
                        "intent": "greeting",
                        "display_name": "Chào hỏi",
                        "description": "Xử lý lời chào",
                        "intent_type": "META",
                    },
                    {
                        "intent": "thank_you",
                        "display_name": "Cảm ơn",
                        "description": "Xử lý lời cảm ơn",
                        "intent_type": "META",
                    },
                ],
                "intent_type": "META",
            }
            
            logger.info(f"Discovered {len(self._domains)} domains with use cases")
            
        except Exception as e:
            logger.error(f"Error discovering use cases: {e}", exc_info=True)
    
    def _format_intent_name(self, intent: str) -> str:
        """Format intent name for display"""
        # Convert snake_case to Title Case
        words = intent.split("_")
        return " ".join(word.capitalize() for word in words)
    
    def _get_intent_description(self, domain: str, intent: str) -> str:
        """Get description for intent"""
        descriptions = {
            "hr": {
                "query_leave_balance": "Tra cứu số ngày phép còn lại",
                "create_leave_request": "Tạo đơn xin nghỉ phép",
                "approve_leave": "Duyệt đơn nghỉ phép",
                "query_salary": "Tra cứu thông tin lương",
            },
            "catalog": {
                "search_products": "Tìm kiếm sản phẩm",
                "query_price": "Tra cứu giá sản phẩm",
            },
            "knowledge": {
                "ask_question": "Hỏi đáp kiến thức",
            },
            "meta": {
                "greeting": "Chào hỏi",
                "thank_you": "Cảm ơn",
            },
        }
        return descriptions.get(domain, {}).get(intent, intent)
    
    def get_all_domains(self) -> List[Dict[str, Any]]:
        """Get all domains with their intents"""
        return list(self._domains.values())
    
    def get_domain(self, domain_name: str) -> Dict[str, Any]:
        """Get specific domain"""
        return self._domains.get(domain_name, {})
    
    def get_all_intents(self) -> List[Dict[str, Any]]:
        """Get all intents across all domains"""
        intents = []
        for domain in self._domains.values():
            for intent in domain.get("intents", []):
                intents.append({
                    **intent,
                    "domain": domain["name"],
                    "domain_display_name": domain["display_name"],
                })
        return intents
    
    def get_intents_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        """Get intents for specific domain"""
        domain = self._domains.get(domain_name, {})
        return domain.get("intents", [])


# Global registry instance
use_case_registry = UseCaseRegistry()

