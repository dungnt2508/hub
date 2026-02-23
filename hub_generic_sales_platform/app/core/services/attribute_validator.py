"""
Attribute Value Validator - Validates attribute values against type and constraints
"""
import re
import json
from typing import Any, Optional, Dict
from fastapi import HTTPException
from app.infrastructure.database.models.knowledge import DomainAttributeDefinition


class AttributeValueValidator:
    """Validator cho attribute values - enforce type safety và constraint validation"""
    
    @staticmethod
    def ensure_single_value(attr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensures check constraint: exactly ONE of value_* columns is non-NULL.
        
        This prevents: IntegrityError on ck_tenant_offering_attr_val_single_value
        
        Args:
            attr_data: Dict with keys like value_text, value_number, value_bool, value_json
                      (may not have all of them)
        
        Returns:
            Cleaned dict with only one non-NULL value
        """
        # Count non-NULL values in the dict
        value_cols = ["value_text", "value_number", "value_bool", "value_json"]
        non_null_count = sum(1 for col in value_cols if attr_data.get(col) is not None)
        
        if non_null_count != 1:
            raise ValueError(
                f"Check constraint violation: exactly 1 value column must be non-NULL, "
                f"but found {non_null_count}. Data keys: {list(attr_data.keys())}"
            )
        
        # Clean up: ensure string "null" is converted to None
        for col in value_cols:
            if col in attr_data and (attr_data[col] == "null" or attr_data[col] == "None"):
                attr_data[col] = None
        
        return attr_data
    
    @staticmethod
    def validate_and_coerce(
        value: Any,
        definition: DomainAttributeDefinition
    ) -> Dict[str, Any]:
        """
        Validate và coerce value theo definition.
        Reject nếu type mismatch (không fallback).
        
        Args:
            value: Raw value từ input
            definition: DomainAttributeDefinition
        
        Returns:
            Dict với key là column name (value_text, value_number, value_bool, value_json)
            và value là coerced value
        
        Raises:
            HTTPException 400 nếu validation fail
        """
        vtype = definition.value_type
        attr_data = {}
        
        # Type coercion (strict, không fallback)
        if vtype == "number":
            try:
                num_value = float(value)
                # Validate constraints trước khi set
                AttributeValueValidator._validate_constraints(num_value, definition)
                attr_data["value_number"] = num_value
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Giá trị '{value}' không thể chuyển đổi sang số cho thuộc tính '{definition.key}'"
                )
        elif vtype == "boolean":
            bool_value = str(value).lower() in ("true", "1", "yes", "on")
            AttributeValueValidator._validate_constraints(bool_value, definition)
            attr_data["value_bool"] = bool_value
        elif vtype == "json":
            try:
                if isinstance(value, str):
                    json_value = json.loads(value)
                elif isinstance(value, (dict, list)):
                    json_value = value
                else:
                    raise ValueError("Invalid JSON value")
                AttributeValueValidator._validate_constraints(json_value, definition)
                attr_data["value_json"] = json_value
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Giá trị '{value}' không phải JSON hợp lệ cho thuộc tính '{definition.key}': {str(e)}"
                )
        else:  # text
            str_value = str(value)
            AttributeValueValidator._validate_constraints(str_value, definition)
            attr_data["value_text"] = str_value
        
        return attr_data
    
    @staticmethod
    def _validate_constraints(value: Any, definition: DomainAttributeDefinition):
        """
        Validate value theo constraints (enum, range, regex).
        
        Raises:
            HTTPException 400 nếu constraint violation
        """
        if not definition.value_constraint:
            return
        
        constraint = definition.value_constraint
        if not isinstance(constraint, dict):
            return  # Skip nếu constraint không phải dict
        
        # Enum validation
        if "enum" in constraint:
            enum_values = constraint["enum"]
            if value not in enum_values:
                raise HTTPException(
                    status_code=400,
                    detail=f"Giá trị '{value}' không nằm trong danh sách cho phép {enum_values} cho thuộc tính '{definition.key}'"
                )
        
        # Range validation (chỉ cho number)
        if "range" in constraint and isinstance(value, (int, float)):
            range_min, range_max = constraint["range"]
            if not (range_min <= value <= range_max):
                raise HTTPException(
                    status_code=400,
                    detail=f"Giá trị '{value}' nằm ngoài phạm vi cho phép [{range_min}, {range_max}] cho thuộc tính '{definition.key}'"
                )
        
        # Regex validation (chỉ cho string)
        if "regex" in constraint and isinstance(value, str):
            pattern = constraint["regex"]
            if not re.match(pattern, value):
                raise HTTPException(
                    status_code=400,
                    detail=f"Giá trị '{value}' không khớp với pattern '{pattern}' cho thuộc tính '{definition.key}'"
                )
