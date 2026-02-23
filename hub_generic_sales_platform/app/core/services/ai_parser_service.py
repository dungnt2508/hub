import json
from typing import Dict, Any, List, Optional
from app.infrastructure.llm.factory import get_llm_provider
import logging

logger = logging.getLogger(__name__)

class AIParserService:
    """
    Uses LLM to transform raw scraped text into structured Offering/Variant data.
    """
    
    def __init__(self):
        self.llm = get_llm_provider()

    async def parse_offering_data(
        self, 
        raw_text: str, 
        attr_definitions: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Uses LLM to extract offering details, guided by Domain Ontology (attr_definitions).
        Returns {"offerings": [...]} - thống nhất với domain (tenant_offering).
        """
        # Build attribute guidance
        attr_guidance = ""
        if attr_definitions:
            attr_guidance = "Ngoài thông tin cơ bản, bạn PHẢI bóc tách các thuộc tính sau nếu có:\n"
            for ad in attr_definitions:
                attr_guidance += f"- {ad.key} ({ad.value_type}): {ad.semantic_type or ''}. \n"

        system_prompt = (
            "Bạn là một chuyên gia về E-commerce Data và Ontology. "
            "Nhiệm vụ của bạn là bóc tách thông tin offering (sản phẩm/dịch vụ) từ nội dung thô của trang web.\n\n"
            "Cấu trúc JSON phản hồi PHẢI như sau:\n"
            "{\n"
            "  \"offerings\": [\n"
            "    {\n"
            "      \"name\": \"Tên offering\",\n"
            "      \"code\": \"Mã offering\",\n"
            "      \"description\": \"Mô tả\",\n"
            "      \"attributes\": { \"key\": \"value\" },\n"
            "      \"variants\": [\n"
            "        { \"sku\": \"SKU\", \"name\": \"Tên biến thể\", \"price\": 100000 }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"{attr_guidance}\n"
            "Lưu ý: "
            "1. Trường 'attributes' chỉ chứa các key đã được liệt kê ở trên. "
            "2. Nếu không có biến thể, tạo 1 biến thể mặc định. "
            "3. Giá là số nguyên (VND)."
        )
        
        user_message = f"Nội dung trang web:\n---\n{raw_text}\n---\nBóc tách offerings theo schema:"
        
        try:
            result = await self.llm.generate_response(
                system_prompt=system_prompt,
                user_message=user_message
            )
            
            content = result.get("response", "")
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed_data = json.loads(content)
            # Chuẩn hóa: LLM có thể trả "products", map sang "offerings" cho thống nhất
            if "offerings" not in parsed_data and "products" in parsed_data:
                parsed_data["offerings"] = parsed_data.pop("products", [])
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing AI data: {str(e)}")
            return {"offerings": []}

    # Alias backward compatibility
    parse_product_data = parse_offering_data
