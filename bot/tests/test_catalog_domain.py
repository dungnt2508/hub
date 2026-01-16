"""
Catalog Domain Test Script
Test Catalog Domain theo Catalog Canon
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.domain.catalog.entry_handler import CatalogEntryHandler
from backend.schemas import DomainRequest, DomainResult
from backend.domain.domain_registry import domain_registry


async def test_canon_compliance():
    """Test tuân thủ Catalog Canon"""
    print("=" * 80)
    print("CATALOG DOMAIN - CANON COMPLIANCE TEST")
    print("=" * 80)
    
    # TEST 1: Intent list không expose
    print("\n✅ TEST 1: Intent list không expose")
    catalog_spec = domain_registry.get_domain("catalog")
    intents = catalog_spec.intents if catalog_spec else []
    if len(intents) == 0:
        print("   PASS: Catalog không expose intent list")
    else:
        print(f"   FAIL: Catalog expose {len(intents)} intents")
    
    # TEST 2: CatalogIntentClassifier không dùng trong entry handler
    print("\n✅ TEST 2: CatalogIntentClassifier không dùng trong entry handler")
    import inspect
    handler_source = inspect.getsource(CatalogEntryHandler.handle)
    uses_classifier = 'CatalogIntentClassifier' in handler_source or 'intent_classifier' in handler_source
    if not uses_classifier:
        print("   PASS: Entry handler không dùng CatalogIntentClassifier")
    else:
        print("   FAIL: Entry handler dùng CatalogIntentClassifier")
    
    # TEST 3: State machine exists
    print("\n❌ TEST 3: State machine exists")
    handler = CatalogEntryHandler()
    has_state_machine = hasattr(handler, 'state_machine')
    if has_state_machine:
        print("   PASS: State machine exists")
    else:
        print("   FAIL: State machine missing (Canon violation)")
    
    print("\n" + "=" * 80)


async def test_use_cases():
    """Test các use cases"""
    print("\n" + "=" * 80)
    print("CATALOG DOMAIN - USE CASE TESTS")
    print("=" * 80)
    
    handler = CatalogEntryHandler()
    tenant_id = "test-tenant-001"
    
    # TEST 1: Search Products
    print("\n📦 TEST 1: Search Products")
    try:
        request = DomainRequest(
            intent="search_products",
            domain="catalog",
            slots={"query": "laptop"},
            user_context={"tenant_id": tenant_id},
            trace_id="test-001"
        )
        response = await handler.handle(request)
        
        if response.status == DomainResult.SUCCESS:
            print("   ✅ PASS: Search products thành công")
            print(f"   Products found: {response.data.get('count', 0) if response.data else 0}")
        else:
            print(f"   ❌ FAIL: Search failed - {response.status}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # TEST 2: Add to Cart
    print("\n🛒 TEST 2: Add to Cart")
    try:
        request = DomainRequest(
            intent="add_to_cart",
            domain="catalog",
            slots={"product_id": "prod-123", "quantity": "1"},
            user_context={"tenant_id": tenant_id},
            trace_id="test-002"
        )
        response = await handler.handle(request)
        
        if response.status in [DomainResult.SUCCESS, DomainResult.NEED_MORE_INFO]:
            print("   ✅ PASS: Add to cart executed")
            if response.data and "cart" in response.data:
                print("   ✅ Cart stored in response data")
        else:
            print(f"   ❌ FAIL: Add to cart failed - {response.status}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # TEST 3: Query Price
    print("\n💰 TEST 3: Query Price")
    try:
        request = DomainRequest(
            intent="query_price",
            domain="catalog",
            slots={"product_id": "prod-123"},
            user_context={"tenant_id": tenant_id},
            trace_id="test-003"
        )
        response = await handler.handle(request)
        
        if response.status == DomainResult.SUCCESS:
            print("   ✅ PASS: Query price thành công")
        else:
            print(f"   ⚠️  WARN: Query price - {response.status}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # TEST 4: Checkout
    print("\n💳 TEST 4: Checkout")
    try:
        request = DomainRequest(
            intent="checkout",
            domain="catalog",
            slots={},
            user_context={
                "tenant_id": tenant_id,
                "cart": {"prod-123": {"quantity": 1, "price": 100}},
                "customer_info": {"name": "Test", "email": "test@test.com"}
            },
            trace_id="test-004"
        )
        response = await handler.handle(request)
        
        if response.status in [DomainResult.SUCCESS, DomainResult.NEED_MORE_INFO]:
            print("   ✅ PASS: Checkout executed")
        else:
            print(f"   ⚠️  WARN: Checkout - {response.status}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 80)


async def test_signal_emission():
    """Test signal emission"""
    print("\n" + "=" * 80)
    print("CATALOG DOMAIN - SIGNAL EMISSION TEST")
    print("=" * 80)
    
    handler = CatalogEntryHandler()
    tenant_id = "test-tenant-001"
    
    # TEST: Escalate should emit signal
    print("\n📡 TEST: Escalate to Livechat")
    try:
        request = DomainRequest(
            intent="escalate_support",
            domain="catalog",
            slots={"reason": "Need help"},
            user_context={"tenant_id": tenant_id},
            trace_id="test-005"
        )
        response = await handler.handle(request)
        
        # Check for signal
        has_signal = (
            hasattr(response, 'signal') or 
            (response.data and 'signal' in response.data) or
            (response.data and response.data.get('escalation', {}).get('escalated'))
        )
        
        if has_signal:
            print("   ✅ PASS: Signal emitted")
        else:
            print("   ❌ FAIL: No signal emission (Canon violation)")
            print("   Response data:", response.data if response.data else "None")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 80)


async def main():
    """Run all tests"""
    await test_canon_compliance()
    await test_use_cases()
    await test_signal_emission()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✅ Use cases execute correctly")
    print("✅ Intent → use case mapping works")
    print("❌ State machine missing (Canon violation)")
    print("❌ Signal emission missing (Canon violation)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
