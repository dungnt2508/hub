"""
Unit tests for Knowledge API schemas – Comparison offering_ids (schema source of truth)
"""
import pytest
from pydantic import ValidationError

from app.interfaces.api.knowledge import ComparisonCreate, ComparisonUpdate, ComparisonResponse


def test_comparison_create_offering_ids_required():
    """offering_ids là required, dùng offering_ids không phải product_ids"""
    data = {
        "domain_id": "dom-1",
        "title": "So sánh",
        "offering_ids": ["off-1", "off-2"],
    }
    obj = ComparisonCreate(**data)
    assert obj.offering_ids == ["off-1", "off-2"]
    assert not hasattr(obj, "product_ids")


def test_comparison_create_offering_ids_empty_list():
    """offering_ids có thể là empty list"""
    obj = ComparisonCreate(title="Empty", offering_ids=[])
    assert obj.offering_ids == []


def test_comparison_create_missing_offering_ids():
    """Thiếu offering_ids → ValidationError"""
    with pytest.raises(ValidationError):
        ComparisonCreate(title="X")


def test_comparison_update_offering_ids_optional():
    """ComparisonUpdate.offering_ids optional"""
    obj = ComparisonUpdate(title="New Title")
    assert obj.offering_ids is None

    obj2 = ComparisonUpdate(offering_ids=["a", "b"])
    assert obj2.offering_ids == ["a", "b"]


def test_comparison_response_offering_ids():
    """ComparisonResponse có offering_ids"""
    data = {
        "id": "comp-1",
        "tenant_id": "t1",
        "domain_id": "d1",
        "title": "T",
        "description": None,
        "offering_ids": ["o1", "o2"],
        "comparison_data": None,
        "is_active": True,
    }
    obj = ComparisonResponse(**data)
    assert obj.offering_ids == ["o1", "o2"]
