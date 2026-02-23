from typing import Dict, Any
import random
from app.core.domain.runtime import LifecycleState
from app.application.services.agent_tool_registry import agent_tools

class EducationStateHandler:
    """
    Education State Handler
    
    Xử lý các nghiệp vụ giáo dục: Kiểm tra trình độ, Tư vấn lộ trình.
    """

    @agent_tools.register_tool(
        name="assessment_test",
        description="Gửi bài kiểm tra trình độ (Assessment Test) hoặc ghi nhận kết quả test nhanh.",
        capability="assessment_test"
    )
    def handle_assessment_test(
        self,
        current_level: str = "Unknown",
        target_score: str = "6.5",
        test_type: str = "Quick",
        **kwargs
    ) -> Dict[str, Any]:
        """Mock Assessment Logic"""
        
        # Mock result generation if "Quick" test
        if test_type == "Quick" and current_level == "Unknown":
            simulated_score = 4.5
            return {
                "success": True,
                "message": f"Đã gửi link bài test nhanh cho bạn...\n[Simulating User doing test]...\nKết quả: Reading/Listening đạt **{simulated_score}**.",
                "level": simulated_score,
                "next_step": "Recommend Foundation Course",
                "new_state": LifecycleState.ANALYZING
            }
        
        return {
            "success": True,
            "message": f"Dựa trên trình độ hiện tại {current_level} và mục tiêu {target_score}, hệ thống đề xuất lộ trình 6 tháng.",
            "new_state": LifecycleState.ANALYZING
        }
