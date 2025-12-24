"""
STEP 1: Meta-task Detection
"""
from typing import Dict, Any

from ...schemas import NormalizedInput, SessionState
from ...shared.logger import logger


class MetaTaskStep:
    """
    Detect and handle meta-tasks (help, reset, greeting, control).
    
    Meta-tasks are system commands, not domain routing.
    """
    
    def __init__(self):
        # Meta-task patterns
        self.meta_patterns = {
            "help": ["giúp", "help", "hướng dẫn", "làm sao"],
            "reset": ["reset", "bắt đầu lại", "làm mới"],
            "greeting": ["xin chào", "chào", "hello", "hi"],
            "goodbye": ["tạm biệt", "bye", "goodbye"],
        }
    
    async def execute(
        self,
        normalized: NormalizedInput,
        session_state: SessionState
    ) -> Dict[str, Any]:
        """
        Detect meta-task.
        
        Args:
            normalized: Normalized input
            session_state: Current session state
            
        Returns:
            Dict with "handled" flag and optional "response"
        """
        message = normalized.normalized_message.lower()
        
        # Check for help
        if any(pattern in message for pattern in self.meta_patterns["help"]):
            return {
                "handled": True,
                "response": "Tôi có thể giúp bạn với các tác vụ về HR, Operations, và nhiều lĩnh vực khác. Bạn muốn làm gì?",
                "type": "META",
            }
        
        # Check for reset
        if any(pattern in message for pattern in self.meta_patterns["reset"]):
            return {
                "handled": True,
                "response": "Đã reset. Bạn muốn làm gì tiếp theo?",
                "type": "META",
            }
        
        # Check for greeting
        if any(pattern in message for pattern in self.meta_patterns["greeting"]):
            return {
                "handled": True,
                "response": "Xin chào! Tôi có thể giúp gì cho bạn?",
                "type": "META",
            }
        
        # Check for goodbye
        if any(pattern in message for pattern in self.meta_patterns["goodbye"]):
            return {
                "handled": True,
                "response": "Tạm biệt! Hẹn gặp lại.",
                "type": "META",
            }
        
        return {"handled": False}

