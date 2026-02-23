import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from app.application.services.semantic_cache_service import SemanticCacheService
from app.core import domain


@pytest.mark.asyncio
async def test_semantic_cache_redis_l1_hit():
    """Sprint 3: Redis L1 cache hit - skip DB, return immediately"""
    db = AsyncMock()
    service = SemanticCacheService(db)
    service.redis_cache.get = AsyncMock(return_value={
        "response_text": "Cached from Redis",
        "cache_id": "cache-123",
    })
    service.cache_repo = MagicMock()
    service.cache_repo.get_by_message = AsyncMock()
    result = await service.find_match("tenant-1", "hello", query_vector=[0.1, 0.2])
    assert result is not None
    assert result.response_text == "Cached from Redis"
    service.cache_repo.get_by_message.assert_not_called()


@pytest.mark.asyncio
async def test_semantic_cache_find_match():
    """L2 DB path when Redis miss"""
    db = AsyncMock()
    service = SemanticCacheService(db)
    service.redis_cache.get = AsyncMock(return_value=None)  # Redis miss
    
    tenant_id = "tenant-1"
    message = "search for red mazda"
    query_vector = [0.1, 0.2, 0.3]
    
    mock_entry = domain.TenantSemanticCache(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        query_text=message,
        response_text="Found Mazda 3",
        hit_count=0
    )
    
    service.cache_repo.get_by_message = AsyncMock(return_value=mock_entry)
    service.redis_cache.set = AsyncMock()
    
    result = await service.find_match(tenant_id, message, query_vector)
    
    assert result is not None
    assert result.response_text == "Found Mazda 3"
    service.cache_repo.get_by_message.assert_called_once_with(
        tenant_id=tenant_id,
        message=message,
        query_vector=query_vector,
        threshold=0.95
    )
    service.redis_cache.set.assert_called_once()

@pytest.mark.asyncio
async def test_semantic_cache_no_match():
    db = AsyncMock()
    service = SemanticCacheService(db)
    service.redis_cache.get = AsyncMock(return_value=None)
    service.cache_repo.get_by_message = AsyncMock(return_value=None)
    
    result = await service.find_match("tenant-1", "random query")
    assert result is None

@pytest.mark.asyncio
async def test_semantic_cache_track_hit():
    """track_hit only when cache_id from DB (Redis hit has no cache_id)"""
    db = AsyncMock()
    service = SemanticCacheService(db)
    service.cache_repo.track_hit = AsyncMock()
    
    cache_id = str(uuid.uuid4())
    await service.track_hit(cache_id)
    
    service.cache_repo.track_hit.assert_called_once_with(cache_id)


@pytest.mark.asyncio
async def test_semantic_cache_track_hit_empty_skipped():
    """Redis L1 hit has no cache_id - track_hit skips"""
    db = AsyncMock()
    service = SemanticCacheService(db)
    service.cache_repo.track_hit = AsyncMock()
    
    await service.track_hit("")
    
    service.cache_repo.track_hit.assert_not_called()

@pytest.mark.asyncio
async def test_semantic_cache_embedding_fallback():
    db = AsyncMock()
    service = SemanticCacheService(db)
    service.redis_cache.get = AsyncMock(return_value=None)
    service.llm_provider.get_embedding = AsyncMock(return_value=[0.5, 0.6])
    service.cache_repo.get_by_message = AsyncMock(return_value=None)
    
    await service.find_match("tenant-1", "hello")
    
    service.llm_provider.get_embedding.assert_called_once_with("hello")
    service.cache_repo.get_by_message.assert_called_once()


@pytest.mark.asyncio
async def test_semantic_cache_create_entry_writes_redis():
    """Sprint 3: create_entry also populates Redis"""
    db = AsyncMock()
    service = SemanticCacheService(db)
    mock_created = domain.TenantSemanticCache(
        id="new-id",
        tenant_id="t1",
        query_text="q",
        response_text="r",
        hit_count=0,
    )
    service.cache_repo.create = AsyncMock(return_value=mock_created)
    service.redis_cache.set = AsyncMock()
    
    await service.create_entry("t1", "q", "r")
    
    service.redis_cache.set.assert_called_once_with(
        "t1", "q", "r", cache_id="new-id"
    )
