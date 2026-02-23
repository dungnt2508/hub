from typing import Dict, Any, List
from app.application.services.agent_tool_registry import agent_tools

class AutoStateHandler:
    """Xử lý các nghiệp vụ liên quan đến Xe cộ (Auto Domain)"""

    @agent_tools.register_tool(
        name="trade_in_valuation",
        description="Định giá xe cũ cho khách hàng dựa trên thông tin xe.",
        capability="trade_in_valuation"
    )
    async def estimate_car_value(self, model: str, year: str, odo: str, condition: str = "Good", **kwargs) -> str:
        """
        Định giá sơ bộ xe cũ.
        Args:
            model: Dòng xe (VD: Mazda 3, Kia Morning)
            year: Năm sản xuất
            odo: Số km đã đi
            condition: Tình trạng (Excellent/Good/Fair)
        """
        # Mock logic định giá
        try:
            year_int = int(year)
            odo_int = int(odo.replace("km", "").replace("vạn", "0000").strip())
        except:
            return "Xin lỗi, tôi cần thông tin Năm sản xuất và ODO chính xác (số) để định giá."

        base_value = 300000000 # Giá sàn 300tr
        
        # Logic đơn giản: Mỗi năm giảm 20tr, mỗi 10000km giảm 10tr
        age = 2026 - year_int
        depreciation_age = age * 20000000
        depreciation_odo = (odo_int / 10000) * 10000000
        
        # Điều chỉnh theo dòng xe
        if "mazda" in model.lower():
            base_value += 100000000
        elif "kia" in model.lower():
            base_value -= 50000000
        
        final_value = base_value - depreciation_age - depreciation_odo
        
        if final_value < 100000000: final_value = 100000000 # Min 100tr
        
        # Format currency
        val_str = "{:,.0f}".format(final_value).replace(",", ".")
        
        return f"Dựa trên thông tin {model} đời {year} đi {odo}km, tôi định giá thu mua sơ bộ khoảng: **{val_str} VNĐ**.\nGiá này có thể thay đổi sau khi kiểm tra thực tế."
