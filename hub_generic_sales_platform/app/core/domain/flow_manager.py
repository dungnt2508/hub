"""
Flow Manager Service - Engine for Dynamic Multi-Industry Conversions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class FlowStep:
    code: str
    description: str
    allowed_tools: List[str]
    next_steps: List[str] # Valid transitions

class FlowManager:
    """
    Manages the logic of moving between steps based on JSON configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.steps = self._parse_config(config)

    def _parse_config(self, config: Dict[str, Any]) -> Dict[str, FlowStep]:
        steps = {}
        for step_data in config.get("steps", []):
            code = step_data["code"]
            steps[code] = FlowStep(
                code=code,
                description=step_data.get("description", ""),
                allowed_tools=step_data.get("allowed_tools", []),
                next_steps=step_data.get("next_steps", [])
            )
        return steps

    def get_step(self, step_code: str) -> Optional[FlowStep]:
        return self.steps.get(step_code)

    def is_transition_valid(self, current_step: str, next_step: str) -> bool:
        step = self.get_step(current_step)
        if not step:
            return False
        return next_step in step.next_steps or next_step == current_step

    def get_allowed_tools(self, current_step: str) -> List[str]:
        step = self.get_step(current_step)
        return step.allowed_tools if step else []
