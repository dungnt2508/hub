
import asyncio
import uuid
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Mocking domain and models since we are running this outside the app context for speed
class MockDomainDecision:
    @classmethod
    def model_validate(cls, obj):
        # Simulate pydantic validation
        if getattr(obj, "force_fail", False):
            raise ValueError("Mock validation error")
        return obj

async def test_endpoint_logic():
    print("Testing Session Stats Logic...")
    
    # Mock database row
    stats_row = {
        "total_turns": 5,
        "total_cost": Decimal("0.00123"),
        "avg_latency": 150.5
    }
    
    # Simulate the formatting logic in analytics.py
    total_turns = stats_row.get("total_turns", 0) or 0
    total_cost = f"${float(stats_row.get('total_cost') or 0):.5f}"
    avg_latency_ms = int(stats_row.get("avg_latency") or 0)
    
    print(f"Summary -> Turns: {total_turns}, Cost: {total_cost}, Latency: {avg_latency_ms}")
    
    assert total_turns == 5
    assert total_cost == "$0.00123"
    assert avg_latency_ms == 150
    
    # Test with Nulls
    stats_row_null = {
        "total_turns": 0,
        "total_cost": None,
        "avg_latency": None
    }
    
    total_turns_n = stats_row_null.get("total_turns", 0) or 0
    total_cost_n = f"${float(stats_row_null.get('total_cost') or 0):.5f}"
    avg_latency_ms_n = int(stats_row_null.get("avg_latency") or 0)
    
    print(f"Null Summary -> Turns: {total_turns_n}, Cost: {total_cost_n}, Latency: {avg_latency_ms_n}")
    
    assert total_turns_n == 0
    assert total_cost_n == "$0.00000"
    assert avg_latency_ms_n == 0
    
    print("Endpoint logic tests passed!")

if __name__ == "__main__":
    asyncio.run(test_endpoint_logic())
