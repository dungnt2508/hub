"""
Script to test Qdrant connection and basic operations
Usage: python -m backend.scripts.test_qdrant_connection
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.infrastructure.vector_store import get_vector_store
from backend.infrastructure.qdrant_client import VectorPoint
from backend.shared.logger import logger


async def test_qdrant_connection():
    """Test Qdrant connection and basic operations"""
    print("=" * 60)
    print("Testing Qdrant Connection")
    print("=" * 60)
    
    # Get vector store
    vector_store = get_vector_store()
    
    # Test 1: Health check
    print("\n1. Health Check...")
    try:
        is_healthy = await vector_store.health_check()
        if is_healthy:
            print("✅ Qdrant is healthy")
        else:
            print("❌ Qdrant health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Create collection
    print("\n2. Creating test collection...")
    test_tenant_id = "test-tenant-00000000-0000-0000-0000-000000000001"
    
    try:
        # Delete if exists first
        if await vector_store.collection_exists(test_tenant_id):
            await vector_store.delete_collection(test_tenant_id)
        
        created = await vector_store.create_collection(test_tenant_id)
        if created:
            print(f"✅ Collection created for tenant: {test_tenant_id}")
        else:
            print(f"ℹ️  Collection already exists for tenant: {test_tenant_id}")
    except Exception as e:
        print(f"❌ Failed to create collection: {e}")
        return False
    
    # Test 3: Upsert vectors
    print("\n3. Upserting test vectors...")
    try:
        test_vectors = [
            VectorPoint(
                id="test-vec-1",
                vector=[0.1] * 1536,  # 1536 dimensions
                metadata={
                    "product_id": "prod-1",
                    "title": "Test Product 1",
                    "description": "This is a test product",
                }
            ),
            VectorPoint(
                id="test-vec-2",
                vector=[0.2] * 1536,
                metadata={
                    "product_id": "prod-2",
                    "title": "Test Product 2",
                    "description": "Another test product",
                }
            ),
        ]
        
        result = await vector_store.upsert_vectors(test_tenant_id, test_vectors)
        if result:
            print(f"✅ Upserted {len(test_vectors)} vectors")
        else:
            print("❌ Failed to upsert vectors")
            return False
    except Exception as e:
        print(f"❌ Failed to upsert vectors: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Search
    print("\n4. Testing search...")
    try:
        query_vector = [0.15] * 1536  # Similar to test vectors
        results = await vector_store.search(
            test_tenant_id,
            query_vector,
            top_k=5,
            score_threshold=0.5
        )
        
        print(f"✅ Search returned {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"   {i}. ID: {result.id}, Score: {result.score:.3f}, Title: {result.metadata.get('title', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to search: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Collection info
    print("\n5. Getting collection info...")
    try:
        info = await vector_store.get_collection_info(test_tenant_id)
        if info:
            print(f"✅ Collection info:")
            print(f"   - Name: {info['name']}")
            print(f"   - Points count: {info['points_count']}")
            print(f"   - Vector size: {info['config']['vector_size']}")
        else:
            print("⚠️  Could not get collection info")
    except Exception as e:
        print(f"❌ Failed to get collection info: {e}")
    
    # Test 6: Cleanup (delete test collection)
    print("\n6. Cleaning up test collection...")
    try:
        deleted = await vector_store.delete_collection(test_tenant_id)
        if deleted:
            print(f"✅ Test collection deleted")
        else:
            print(f"⚠️  Test collection was not deleted (may not have existed)")
    except Exception as e:
        print(f"⚠️  Failed to delete test collection: {e}")
        print("   (This is OK, you can delete manually if needed)")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_qdrant_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

