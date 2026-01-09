"""
Phase 1 Demo: Message → Route Decision → Trace

Demonstrates complete routing flow from user message to routing decision
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.router.orchestrator import RouterOrchestrator
from backend.schemas import RouterRequest


async def print_response(response):
    """Pretty print router response"""
    print("\n" + "=" * 70)
    print(f"📍 ROUTING DECISION")
    print("=" * 70)
    print(f"✓ Session ID:     {response.session_id}")
    print(f"✓ Trace ID:       {response.trace_id}")
    print(f"✓ Domain:         {response.domain}")
    print(f"✓ Intent:         {response.intent}")
    print(f"✓ Confidence:     {response.confidence:.2f}" if response.confidence else "✓ Confidence:     N/A")
    print(f"✓ Source:         {response.source}")
    
    if response.routing_trace:
        print(f"\n📋 ROUTING TRACE ({len(response.routing_trace)} steps):")
        for i, trace in enumerate(response.routing_trace, 1):
            step = trace.get("step", "unknown")
            result = trace.get("result", {})
            print(f"   Step {i}: {step}")
            if result.get("matched"):
                print(f"      ✓ Matched: {result.get('matched')}")
            if result.get("classified"):
                print(f"      ✓ Classified: {result.get('classified')}")
            if result.get("score"):
                print(f"      ✓ Score: {result.get('score'):.2f}")


async def demo_scenario(router, scenario_num, message, user_id=None):
    """Run a demo scenario"""
    print(f"\n{'=' * 70}")
    print(f"📝 SCENARIO {scenario_num}: {message}")
    print(f"{'=' * 70}")
    
    request = RouterRequest(
        user_id=user_id or f"demo-user-{scenario_num}",
        raw_message=message,
        session_id=None
    )
    
    try:
        response = await router.route(request)
        await print_response(response)
        return response
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def demo_session_persistence(router):
    """Demo session persistence"""
    print(f"\n{'=' * 70}")
    print("🔄 SESSION PERSISTENCE TEST")
    print(f"{'=' * 70}")
    
    user_id = "session-demo-user"
    
    # Request 1
    print("\n📝 Request 1: Create session")
    request1 = RouterRequest(
        user_id=user_id,
        raw_message="Tôi muốn xin phép",
        session_id=None
    )
    response1 = await router.route(request1)
    session_id = response1.session_id
    print(f"✓ Session created: {session_id}")
    
    # Request 2
    print("\n📝 Request 2: Reuse same session")
    request2 = RouterRequest(
        user_id=user_id,
        raw_message="Bao nhiêu ngày phép?",
        session_id=session_id
    )
    response2 = await router.route(request2)
    
    if response2.session_id == session_id:
        print(f"✓ Session persisted: {response2.session_id}")
    else:
        print(f"❌ Session mismatch!")


async def main():
    """Run Phase 1 demo"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 1 DEMO - GLOBAL ROUTER SYSTEM" + " " * 19 + "║")
    print("║" + " " * 20 + "Message → Routing Decision → Trace" + " " * 14 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Initialize router
    print("\n🚀 Initializing router...")
    try:
        router = RouterOrchestrator()
        print("✓ Router initialized")
    except Exception as e:
        print(f"❌ Failed to initialize router: {e}")
        return
    
    # Demo scenarios
    scenarios = [
        (1, "Tôi còn bao nhiêu ngày phép?"),  # Leave balance query
        (2, "Tôi muốn xin phép từ ngày 1/2 đến 5/2"),  # Leave request
        (3, "Tìm sản phẩm điện thoại"),  # Catalog search
        (4, "Xin chào"),  # Generic greeting
        (5, "xyz abc def"),  # Unknown
    ]
    
    responses = []
    for scenario_num, message in scenarios:
        response = await demo_scenario(router, scenario_num, message)
        if response:
            responses.append(response)
        await asyncio.sleep(0.5)
    
    # Session persistence demo
    await demo_session_persistence(router)
    
    # Summary
    print(f"\n{'=' * 70}")
    print("📊 DEMO SUMMARY")
    print(f"{'=' * 70}")
    print(f"✓ Total scenarios: {len(scenarios)}")
    print(f"✓ Successful routes: {len(responses)}")
    
    hr_count = sum(1 for r in responses if r.domain == "hr")
    catalog_count = sum(1 for r in responses if r.domain == "catalog")
    other_count = len(responses) - hr_count - catalog_count
    
    if hr_count > 0:
        print(f"✓ HR domain routes: {hr_count}")
    if catalog_count > 0:
        print(f"✓ Catalog domain routes: {catalog_count}")
    if other_count > 0:
        print(f"✓ Other/Unknown routes: {other_count}")
    
    # Performance
    total_confidence = sum(r.confidence for r in responses if r.confidence)
    avg_confidence = total_confidence / len(responses) if responses else 0
    print(f"✓ Average confidence: {avg_confidence:.2f}")
    
    print(f"\n{'=' * 70}")
    print("✅ DEMO COMPLETE - Phase 1 routing system working!")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())

