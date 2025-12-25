"""
Example: Basic Router Usage
"""
import asyncio
import uuid
from backend.router import RouterOrchestrator
from backend.types import RouterRequest


async def main():
    """Example usage of router"""
    # Initialize router
    router = RouterOrchestrator()
    
    # Create request
    request = RouterRequest(
        raw_message="Tôi còn bao nhiêu ngày phép?",
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),  # Task 7: tenant_id is now required
    )
    
    # Route request
    response = await router.route(request)
    
    # Print response
    print(f"Status: {response.status}")
    print(f"Domain: {response.domain}")
    print(f"Intent: {response.intent}")
    print(f"Message: {response.message}")
    print(f"Trace ID: {response.trace_id}")


if __name__ == "__main__":
    asyncio.run(main())

