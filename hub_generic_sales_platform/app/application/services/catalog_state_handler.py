from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

# Domain Import Layer
from app.core import domain
from app.core.domain.runtime import LifecycleState, SlotKey
from app.core.domain.decision import DecisionType

from app.infrastructure.database.repositories import ContextSlotRepository
from app.infrastructure.database.repositories import OfferingRepository, OfferingAttributeRepository
from app.infrastructure.database.repositories import ComparisonRepository
from app.application.services.agent_tool_registry import agent_tools
from app.core.services.catalog_service import CatalogService
from app.infrastructure.llm.factory import get_llm_provider
import re

class CatalogStateHandler:
    """
    Catalog State Handler (Async Implementation)
    
    Xử lý các hành động sản phẩm dựa trên Domain Entities.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.slot_repo = ContextSlotRepository(db)
        self.catalog_service = CatalogService(db)
        self.comparison_repo = ComparisonRepository(db)
        self.offering_repo = OfferingRepository(db)
        self.attr_repo = OfferingAttributeRepository(db)
    
    @agent_tools.register_tool(
        name="search_offerings",
        description="Tìm sản phẩm. Dùng ngay khi người dùng hỏi 'có...không' hoặc đề cập tên/loại sản phẩm.",
        capability="offering_search"
    )
    async def handle_search_offerings(
        self,
        query: Optional[str] = None, # Từ khóa (VD: 'Mazda', 'Vay', 'IELTS')
        **kwargs
    ) -> Dict[str, Any]:
        """Tìm kiếm offering (Async)"""
        session = kwargs.get("session")
        if not session:
            return {"success": False, "error": "Missing session context"}
            
        # Use message as fallback when query is None (agent called search without keyword)
        if query is None or (isinstance(query, str) and not query.strip()):
            query = str(kwargs.get("message", "") or "").strip() or None

        # Resolve ordinal reference if any (e.g., "xe 1", "cái thứ 2")
        history = kwargs.get("history", [])
        resolved_query = self._resolve_ordinal_reference(query, history)
        if resolved_query:
            print(f"[AGENT-LOG] Resolved ordinal '{query}' -> '{resolved_query}'")
            query = resolved_query
        
        tenant_id = session.tenant_id
        offerings = await self.catalog_service.offering_repo.get_active_offerings(tenant_id)
        
        if not offerings:
            return {
                "success": True, 
                "offerings": [], 
                "message": "Xin lỗi, hiện không có sản phẩm hoặc dịch vụ nào đang kinh doanh."
            }
            
        result = []
        query_text = query.lower().strip() if query else ""
        
        # 1. Substring search (nhanh)
        for o in offerings:
            version = await self.catalog_service.version_repo.get_active_version(o.id, tenant_id=tenant_id)
            if version:
                match = True
                if query_text:
                    text_to_search = f"{o.code} {version.name} {version.description}".lower()
                    if query_text not in text_to_search:
                        match = False
                
                if match:
                    result.append({
                        "id": o.id,
                        "code": o.code,
                        "type": o.type,
                        "name": version.name,
                        "summary": version.description[:100] + "..." if version.description else ""
                    })
        
        # 2. Semantic search fallback: khi không có kết quả và query nhiều từ (ý đồ tìm kiếm phức tạp)
        if not result and query_text and len(query_text.split()) >= 2:
            try:
                llm = get_llm_provider()
                query_vector = await llm.get_embedding(query or "")
                sem_versions = await self.catalog_service.version_repo.semantic_search(
                    tenant_id, query_vector, threshold=0.75, limit=10
                )
                seen_ids = set()
                for ver, _ in sem_versions:
                    off = await self.catalog_service.offering_repo.get(ver.offering_id, tenant_id=tenant_id)
                    if off and off.id not in seen_ids:
                        seen_ids.add(off.id)
                        result.append({
                            "id": off.id,
                            "code": off.code,
                            "type": off.type,
                            "name": ver.name,
                            "summary": (ver.description or "")[:100] + "..."
                        })
            except Exception as e:
                print(f"[AGENT-LOG] Semantic search fallback error: {e}")
            
        print(f"[AGENT-LOG] Search Query: '{query or '(empty)'}' | Found: {len(result)} items")
        
        if not result and query:
             return {
                "success": True, 
                "offerings": [], 
                "message": f"Không tìm thấy sản phẩm nào phù hợp với từ khóa '{query}'."
             }

        # 3. Ghi slots từ kết quả search (giúp "nó", "cái này" map đúng)
        session_id = str(getattr(session, "id", "") or "")
        if session_id and result:
            try:
                await self._upsert_search_slots(
                    session_id, tenant_id, result
                )
            except Exception as e:
                print(f"[AGENT-LOG] Slot upsert skip: {e}")

        return {
            "success": True, 
            "offerings": result,
            "count": len(result),
            "new_state": LifecycleState.SEARCHING
        }

    @agent_tools.register_tool(
        name="get_offering_details",
        description="Lấy thông tin đầy đủ nhất của offering (sản phẩm/dịch vụ) bao gồm Giá hiện hành, Tồn kho và Thông số chi tiết.",
        capability="offering_details"
    )
    async def handle_get_offering_details(
        self,
        offering_code: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Lấy chi tiết offering hợp nhất (Generic)"""
        session = kwargs.get("session")
        if not session:
            return {"success": False, "error": "Missing session context"}
            
        tenant_id = session.tenant_id
        channel_code = session.ext_metadata.get("channel", "WEB") if session.ext_metadata else "WEB"
        
        # Resolve ordinal reference
        history = kwargs.get("history", [])
        resolved_code = self._resolve_ordinal_reference(offering_code, history)
        if resolved_code:
            print(f"[AGENT-LOG] Resolved ordinal '{offering_code}' -> '{resolved_code}'")
            offering_code = resolved_code
            
        # Fallback to Slots if offering_code is missing or ambiguous
        if not offering_code or offering_code.lower().strip() in ["nó", "cái này", "sản phẩm này", "đó"]:
            context_slots = kwargs.get("context_slots", [])
            slot_value = None
            slot_key_used = None
            for slot in context_slots:
                if slot.key in [SlotKey.OFFERING_CODE, "product_code", "product_id", SlotKey.OFFERING_ID]:
                    slot_value = slot.value
                    slot_key_used = slot.key
                    break
            if slot_value:
                # Resolve offering_id/product_id (UUID) -> code; offering_code/product_code -> use as-is
                if slot_key_used in [SlotKey.OFFERING_ID, "product_id"]:
                    offering = await self.offering_repo.get(str(slot_value), tenant_id=tenant_id)
                    if offering:
                        offering_code = offering.code
                        print(f"[AGENT-LOG] Fallback Slot '{slot_key_used}' (UUID) -> code: {offering_code}")
                    else:
                        offering_code = str(slot_value)
                        print(f"[AGENT-LOG] Fallback Slot '{slot_key_used}': {offering_code} (ID not found, try as code)")
                else:
                    offering_code = str(slot_value)
                    print(f"[AGENT-LOG] Fallback Slot '{slot_key_used}': {offering_code}")
        
        if not offering_code:
             return {
                "success": False, 
                "message": "Vui lòng cho biết bạn muốn xem chi tiết sản phẩm nào?"
            }

        offering_data = await self.catalog_service.get_offering_for_bot(tenant_id, str(offering_code), channel_code)
        
        if not offering_data:
            return {
                "success": False, 
                "message": f"Không tìm thấy thông tin {offering_code}"
            }
            
        attrs = await self.attr_repo.get_by_version(offering_data["version_id"], tenant_id=tenant_id)
        
        offering_data["specifications"] = {
            a.definition.key if a.definition else "unknown": 
            a.value_text or str(a.value_number) or str(a.value_bool) or "N/A" 
            for a in attrs
        }
        
        return {
            "success": True,
            "offering": offering_data,
            "new_state": LifecycleState.VIEWING
        }
    
    @agent_tools.register_tool(
        name="compare_offerings",
        description="So sánh 2 offering dựa trên context/slots hiện tại.",
        capability="offering_comparison"
    )
    async def handle_compare_action(
        self,
        message: str,
        session: domain.RuntimeSession,
        context_slots: List[domain.RuntimeContextSlot],
        **kwargs
    ) -> Dict[str, Any]:

        """Xử lý so sánh offering (Async)"""
        offering_slots = self._get_offering_slots(context_slots)
        
        if len(offering_slots) < 2:
            return {
                "success": False,
                "decision_type": DecisionType.REQUEST_REFERENCE_CLARIFICATION,
                "response": "Để so sánh, bạn cần ít nhất 2 đối tượng. Vui lòng chọn thêm."
            }
        
        offering_ids = [s.get(SlotKey.OFFERING_ID) for s in offering_slots if s.get(SlotKey.OFFERING_ID)]
        tenant_id = session.tenant_id
        
        comparisons = await self.comparison_repo.get_by_offerings(tenant_id, offering_ids)
        if comparisons:
            comp = comparisons[0]
            offerings_for_ui = await self._get_offerings_for_ui(tenant_id, offering_ids)
            return {
                "success": True,
                "decision_type": DecisionType.PROCEED,
                "response": comp.description or f"So sánh {comp.title}",
                "g_ui_data": {
                    "type": "bento_grid",
                    "data": {
                        "title": comp.title,
                        "products": offerings_for_ui # Bento grid expects 'products' key usually, keep for compatibility
                    }
                } if offerings_for_ui else None
            }
        
        offerings_data = []
        for o_id in offering_ids:
            o = await self.offering_repo.get(o_id, tenant_id)
            if o:
                version = await self.catalog_service.version_repo.get_active_version(o.id, tenant_id=tenant_id)
                if version:
                    attrs = await self.attr_repo.get_by_version(version.id, tenant_id=tenant_id)
                    attr_dict = {
                        a.definition.key if a.definition else "unknown": 
                        a.value_text or str(a.value_number) or str(a.value_bool) or "N/A" 
                        for a in attrs
                    }
                    offerings_data.append({
                        "id": o.id,
                        "name": version.name,
                        "code": o.code,
                        "description": version.description,
                        "attributes": attr_dict
                    })
        
        if len(offerings_data) < 2:
            return {"success": False, "response": "Không đủ thông tin để so sánh."}
        
        offerings_for_ui = []
        for o in offerings_data:
            price = o["attributes"].get("price", "N/A")
            offerings_for_ui.append({
                "id": o["id"],
                "name": o["name"],
                "price": str(price),
                "tags": [k for k in o["attributes"].keys() if k != "price"][:3] 
            })
            
        return {
            "success": True,
            "decision_type": DecisionType.PROCEED,
            "response": self._format_comparison_response(offerings_data),
            "g_ui_data": {
                "type": "bento_grid",
                "data": {
                    "title": f"So sánh {offerings_data[0]['name']} và {offerings_data[1]['name']}",
                    "products": offerings_for_ui
                }
            } if offerings_for_ui else None
        }
    
    async def _upsert_search_slots(
        self, session_id: str, tenant_id: str, result: List[Dict]
    ) -> None:
        """Ghi slots từ kết quả search để 'nó', 'cái này' map đúng offering."""
        from app.core.domain.runtime import SlotStatus, SlotSource
        await self.slot_repo.deactivate_by_keys(
            session_id, [SlotKey.OFFERING_ID], tenant_id
        )
        first = result[0]
        await self.slot_repo.create({
            "session_id": session_id,
            "key": SlotKey.OFFERING_ID,
            "value": str(first["id"]),
            "status": SlotStatus.ACTIVE.value,
            "source": SlotSource.INFERRED.value
        })

    def _get_offering_slots(self, slots: List[domain.RuntimeContextSlot]) -> List[Dict]:
        return [{SlotKey.OFFERING_ID: s.value} for s in slots if SlotKey.OFFERING_ID in s.key.lower() or "product_id" in s.key.lower()]
    
    def _format_comparison_response(self, data: List[Dict]) -> str:
        p1, p2 = data[0], data[1]
        res = [f"So sánh {p1['name']} và {p2['name']}:\n"]
        common = set(p1["attributes"].keys()) & set(p2["attributes"].keys())
        for k in common:
            if p1["attributes"][k] != p2["attributes"][k]:
                res.append(f"- {k}: {p1['attributes'][k]} vs {p2['attributes'][k]}")
        return "\n".join(res)
    
    async def _get_offerings_for_ui(self, tenant_id: str, offering_ids: List[str]) -> List[Dict[str, Any]]:
        """Lấy thông tin offering để hiển thị trong BentoGrid"""
        offerings_for_ui = []
        for o_id in offering_ids:
            o = await self.offering_repo.get(o_id, tenant_id)
            if o:
                version = await self.catalog_service.version_repo.get_active_version(o.id, tenant_id=tenant_id)
                if version:
                    attrs = await self.attr_repo.get_by_version(version.id, tenant_id=tenant_id)
                    attr_dict = {
                        a.definition.key if a.definition else "unknown": 
                        a.value_text or str(a.value_number) or str(a.value_bool) or "N/A" 
                        for a in attrs
                    }
                    price = attr_dict.get("price", "N/A")
                    offerings_for_ui.append({
                        "id": o.id,
                        "name": version.name,
                        "price": str(price),
                        "tags": [k for k in attr_dict.keys() if k != "price"][:3] 
                    })

        return offerings_for_ui

    def _resolve_ordinal_reference(self, query: str, history: List[Dict]) -> Optional[str]:
        """
        Detects references like "xe 1", "cái thứ 2", "số 3" and maps them to product names
        from the last Bot message containing a numbered list.
        Skips product names containing numbers (e.g. "Toyota Camry 2.0Q 2022").
        """
        if not query or not history:
            return None

        q_lower = query.strip().lower()
        # Skip long queries that look like product names (avoid matching "2" in "2.0Q" or "2022")
        if len(q_lower.split()) > 3 and not re.match(r'^(?:xe|cái|số|mẫu|sản phẩm|thứ)\s+\d+$', q_lower):
            return None

        # 1. Only match explicit ordinal: "1", "2", "xe 1", "cái 2" - NOT "2.0", "2022"
        # Require: 1-2 digit index (1-99), not part of version (2.0) or year (2022)
        match = re.search(r'(?:^|\s)(?:xe|cái|số|mẫu|sản phẩm|thứ)\s+([1-9]\d?)(?:\s|$)|(?:^|\s)([1-9]\d?)(?:\s|$)', q_lower)
        if not match:
            return None
        index = int(match.group(1) or match.group(2))
        
        # 2. Look backwards for the last Bot message
        for turn in reversed(history):
            if turn["role"] == "assistant":
                content = turn["content"]
                # 3. Parse numbered list in bot message
                # Regex to find lines starting with "1.", "1)", etc.
                # Example: "1. **Mazda 3**..." or "1. Mazda 3"
                list_items = re.findall(r'^\s*(\d+)[\.\)]\s+(.+)$', content, re.MULTILINE)
                
                for idx_str, item_text in list_items:
                    if int(idx_str) == index:
                        # Extract the main name (often bolded or first distinct part)
                        # Remove markdown bolding
                        clean_text = item_text.replace("**", "").strip()
                        # Take the first part before a colon or newline if any (simple heuristic)
                        if ":" in clean_text:
                            clean_text = clean_text.split(":")[0].strip()
                        return clean_text
                        
        return None
