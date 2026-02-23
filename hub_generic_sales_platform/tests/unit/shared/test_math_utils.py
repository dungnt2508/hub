import pytest
from app.core.shared.math_utils import cosine_similarity

pytestmark = pytest.mark.unit

def test_cosine_similarity_edge_cases():
    """Test math utils with various vector inputs"""
    # Identical vectors
    v1 = [1, 0, 1]
    v2 = [1, 0, 1]
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)
    
    # Orthogonal vectors
    v3 = [1, 0]
    v4 = [0, 1]
    assert cosine_similarity(v3, v4) == 0.0
    
    # Empty or None
    assert cosine_similarity([], [1]) == 0.0
    assert cosine_similarity(None, [1]) == 0.0
    
    # Different lengths
    assert cosine_similarity([1, 1], [1, 1, 1]) == 0.0

def test_cosine_similarity_precision():
    """Test similarity with real embedding-like values"""
    v1 = [0.1, 0.2, 0.3]
    v2 = [0.2, 0.4, 0.6] # Same direction, different magnitude
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)
