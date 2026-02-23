"""Flow Tracer - Log input/output c逶ｻ・ｧa t逶ｻ・ｫng b・・ｽｰ逶ｻ雖ｩ trong 15-step flow"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class FlowStep:
    """Represents a single step in the flow"""
    
    def __init__(self, step_number: int, step_name: str):
        self.step_number = step_number
        self.step_name = step_name
        self.input: Dict[str, Any] = {}
        self.output: Dict[str, Any] = {}
        self.timestamp = datetime.now()
        self.duration_ms: Optional[float] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "step": self.step_number,
            "name": self.step_name,
            "input": self.input,
            "output": self.output,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error": self.error
        }


class FlowTracer:
    """
    Flow Tracer - Trace v・・｣ｰ log t逶ｻ・ｫng b・・ｽｰ逶ｻ雖ｩ trong 15-step flow
    
    Usage:
        tracer = FlowTracer()
        with tracer:
            result = handler.handle_message(...)
        tracer.print_summary()
        tracer.save_to_file("flow_trace.json")
    """
    
    STEPS = [
        (1, "Nh陂ｯ・ｭn tin nh陂ｯ・ｯn 遶翫・conversation_turn"),
        (2, "・・妛・ｻ逧・session state"),
        (3, "Routing qua intent (IntentResolver)"),
        (4, "Tr・・ｽｭch xu陂ｯ・･t slot (SlotExtractor)"),
        (5, "Chu陂ｯ・ｩn ho・・ｽ｡ slot (SlotNormalizer)"),
        (6, "Ki逶ｻ繝・tra slot (SlotValidator)"),
        (7, "Ki逶ｻ繝・tra guardrails (GuardrailChecker)"),
        (8, "Ra decision (DecisionEngine)"),
        (9, "Chuy逶ｻ繝・session state (n陂ｯ・ｿu c陂ｯ・ｧn)"),
        (10, "L陂ｯ・ｭp k陂ｯ・ｿ ho陂ｯ・｡ch truy v陂ｯ・･n (QueryPlanner)"),
        (11, "Truy v陂ｯ・･n knowledge (KnowledgeQueryExecutor)"),
        (12, "Ph・・ｽ｢n t・・ｽｭch k陂ｯ・ｿt qu陂ｯ・｣"),
        (13, "X陂ｯ・ｿp h陂ｯ・｡ng"),
        (14, "Tr・・ｽｬnh b・・｣ｰy k陂ｯ・ｿt qu陂ｯ・｣"),
        (15, "Ghi turn bot")
    ]
    
    def __init__(self, enabled: bool = True):
        """
        Args:
            enabled: Enable/disable tracing
        """
        self.enabled = enabled
        self.steps: List[FlowStep] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.final_result: Optional[Dict[str, Any]] = None
    
    def __enter__(self):
        """Context manager entry"""
        if self.enabled:
            self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.enabled:
            self.end_time = datetime.now()
        return False
    
    def log_step(
        self,
        step_number: int,
        step_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        error: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """Log a step"""
        if not self.enabled:
            return
        
        step = FlowStep(step_number, step_name)
        step.input = self._sanitize_data(input_data)
        step.output = self._sanitize_data(output_data)
        step.error = error
        step.duration_ms = duration_ms
        self.steps.append(step)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data for logging (remove sensitive info, convert objects)"""
        if data is None:
            return None
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Skip sensitive fields
                if key in ["api_key", "password", "secret", "token"]:
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        
        if isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        
        # Convert objects to dict if possible
        if hasattr(data, "__dict__"):
            return self._sanitize_data(data.__dict__)
        
        # Convert UUID/ID objects to string
        if hasattr(data, "__str__"):
            try:
                return str(data)
            except:
                pass
        
        return data
    
    def set_final_result(self, result: Dict[str, Any]):
        """Set final result"""
        self.final_result = self._sanitize_data(result)
    
    def print_summary(self):
        """Print summary of all steps"""
        if not self.enabled or not self.steps:
            return
        
        print("\n" + "="*80)
        print("FLOW TRACE SUMMARY - 15 B・・ｽｯ逶ｻ蜥ｾ")
        print("="*80)
        
        for step in self.steps:
            status = "隨ｶ繝ｻERROR" if step.error else "隨ｨ繝ｻOK"
            duration = f" ({step.duration_ms:.2f}ms)" if step.duration_ms else ""
            
            print(f"\nB・・ｽｰ逶ｻ雖ｩ {step.step_number}: {step.step_name} {status}{duration}")
            print(f"  Input: {json.dumps(step.input, indent=2, ensure_ascii=False)}")
            print(f"  Output: {json.dumps(step.output, indent=2, ensure_ascii=False)}")
            
            if step.error:
                print(f"  Error: {step.error}")
        
        if self.final_result:
            print(f"\n{'='*80}")
            print("FINAL RESULT:")
            print(f"{'='*80}")
            print(json.dumps(self.final_result, indent=2, ensure_ascii=False))
        
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds() * 1000
            print(f"\n{'='*80}")
            print(f"TOTAL DURATION: {total_duration:.2f}ms")
            print("="*80)
        
        print()
    
    def save_to_file(self, filepath: str):
        """Save trace to JSON file"""
        if not self.enabled:
            return
        
        trace_data = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [step.to_dict() for step in self.steps],
            "final_result": self.final_result
        }
        
        if self.start_time and self.end_time:
            trace_data["total_duration_ms"] = (self.end_time - self.start_time).total_seconds() * 1000
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace_data, f, indent=2, ensure_ascii=False)
        
        print(f"Flow trace saved to: {filepath}")
    
    def get_step(self, step_number: int) -> Optional[FlowStep]:
        """Get step by number"""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    def get_summary_dict(self) -> Dict[str, Any]:
        """Get summary as dictionary"""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_steps": len(self.steps),
            "steps": [step.to_dict() for step in self.steps],
            "final_result": self.final_result
        }
