from typing import Dict, Any
import random
from app.core.domain.runtime import LifecycleState
from app.application.services.agent_tool_registry import agent_tools
from app.core.services.price_service import price_service

class FinancialStateHandler:
    """
    Financial State Handler
    
    Xử lý các hành động liên quan đến tài chính: Tra cứu giá Real-time, Phân tích thị trường.
    """
    
    @agent_tools.register_tool(
        name="get_market_data",
        description="Tra cứu giá VÀNG hoặc CỔ PHIẾU (Real-time). Chỉ dùng khi user hỏi mã CK (VD: 'VNM', 'FPT') hoặc giá vàng. KHÔNG dùng cho giá sản phẩm/xe cộ.",
        capability="market_data_realtime"
    )
    async def handle_get_market_data(
        self,
        symbol: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Fetch actual real-time market data"""
        symbol = symbol.upper()
        
        # 1. Gold Logic
        if "SJC" in symbol or "VÀNG" in symbol:
            data = await price_service.get_gold_price()
            if "error" in data:
                return {"success": False, "message": "Hiện tại không thể lấy giá vàng. Vui lòng thử lại sau."}
            
            note = f"\n(Lưu ý: {data['note']})" if "note" in data else ""
            return {
                "success": True,
                "symbol": "SJC",
                "name": data["name"],
                "price_buy": data["buy"],
                "price_sell": data["sell"],
                "unit": data["unit"],
                "updated_at": data["updated_at"],
                "message": f"Giá vàng SJC hiện tại: Mua vào {data['buy']} - Bán ra {data['sell']} ({data['unit']}).{note}",
                "g_ui_data": {
                    "type": "market_card",
                    "data": {
                        "symbol": "SJC",
                        "buy": data["buy"],
                        "sell": data["sell"],
                        "unit": data["unit"],
                        "note": data.get("note")
                    }
                }
            }

        data = await price_service.get_stock_price(symbol)
        if "error" in data or data.get("price") == "N/A":
             return {"success": False, "message": f"Không tìm thấy thông tin cho mã {symbol} hoặc dịch vụ đang bảo trì."}

        note = f"\n(Lưu ý: {data['note']})" if "note" in data else ""
        return {
            "success": True,
            "symbol": symbol,
            "name": f"Cổ phiếu {symbol}",
            "price": data["price"],
            "change": data["change"],
            "unit": data["unit"],
            "message": f"Giá cổ phiếu {symbol} hiện tại là {data['price']} {data['unit']} (Biến động: {data['change']}).{note}",
            "g_ui_data": {
                "type": "market_card",
                "data": {
                    "symbol": symbol,
                    "price": data["price"],
                    "change": data["change"],
                    "unit": data["unit"],
                    "note": data.get("note")
                }
            }
        }

    @agent_tools.register_tool(
        name="get_strategic_analysis",
        description="Cung cấp nhận định chiến lược và phân tích xu hướng thị trường cho một mã hoặc lĩnh vực.",
        capability="strategic_analysis"
    )
    async def handle_strategic_analysis(
        self,
        topic: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock behavior for strategic analysis"""
        
        analysis_map = {
            "VÀNG": "Xu hướng vàng thế giới đang ổn định, ngân hàng trung ương mua ròng. Khuyến nghị nắm giữ trung hạn.",
            "CHỨNG KHOÁN": "Thị trường đang trong giai đoạn tích lũy, cơ hội ở nhóm ngành sản xuất và xuất khẩu.",
            "VNM": "Vinamilk đang cải thiện biên lợi nhuận, phù hợp cho danh mục phòng thủ."
        }
        
        topic_upper = topic.upper()
        analysis = "Chúng tôi đang tổng hợp dữ liệu mới nhất. Nhìn chung thị trường vẫn đang giữ nhịp ổn định."
        for key in analysis_map:
            if key in topic_upper:
                analysis = analysis_map[key]
                break

        return {
            "success": True,
            "topic": topic,
            "analysis": analysis,
            "g_ui_data": {
                "type": "analysis_insight",
                "data": {
                    "title": f"Nhận định chiến lược: {topic}",
                    "content": analysis,
                    "confidence": "High"
                }
            }            
        }

    @agent_tools.register_tool(
        name="credit_scoring",
        description="Chấm điểm tín dụng sơ bộ dựa trên thu nhập, địa điểm và lịch sử nợ.",
        capability="credit_scoring"
    )
    async def handle_credit_scoring(
        self,
        income: str,
        location: str,
        debt_status: str = "None",
        **kwargs
    ) -> Dict[str, Any]:
        """Mock behavior for Credit Scoring"""
        
        # Simple Logic
        score = 600
        
        try:
            inc_val = int(str(income).replace("triệu", "000000").replace(".","").replace(",",""))
        except:
            inc_val = 10000000 # Default 10m
            
        if inc_val > 15000000: score += 100
        if "Hà Nội" in location or "HCM" in location: score += 50
        if "nợ xấu" in debt_status.lower(): score -= 200
        
        status = "Good" if score >= 650 else ("Fair" if score >= 500 else "Poor")
        
        limit = 0
        if status == "Good": limit = 50000000
        elif status == "Fair": limit = 20000000
        
        return {
            "success": True,
            "score": score,
            "status": status,
            "suggested_limit": limit,
            "message": f"Dựa trên hồ sơ (Thu nhập {income}, KV {location}), điểm tín dụng của bạn là **{score} ({status})**.\nHạn mức đề xuất: **{limit:,} VNĐ**.",
            "g_ui_data": {
                "type": "credit_card",
                "data": {
                    "score": score,
                    "status": status,
                    "limit": limit
                }
            }
        }
