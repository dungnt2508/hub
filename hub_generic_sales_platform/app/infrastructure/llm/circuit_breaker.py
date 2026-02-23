import logging
from circuitbreaker import CircuitBreaker

logger = logging.getLogger(__name__)

class LLMCircuitBreaker(CircuitBreaker):
    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 30  # seconds
    
    def __init__(self):
        super().__init__(name="LLMCircuitBreaker")
        
llm_circuit = LLMCircuitBreaker()
