"""
Collect Customer Info Use Case
"""
from typing import Optional, Dict, Any
import re
from ....schemas import DomainRequest, DomainResponse, DomainResult
from .base_use_case import CatalogUseCase
from ....shared.logger import logger


class CollectCustomerInfoUseCase(CatalogUseCase):
    """
    Collect customer information for checkout.
    
    Use case: User is checking out and needs to provide:
    - Name
    - Email
    - Phone
    - Address
    - Payment method (optional)
    
    This use case handles multi-turn form collection with validation.
    """
    
    def __init__(self, repository=None):
        """
        Initialize collect customer info use case.
        
        Args:
            repository: Not used for this use case, but required by base class
        """
        pass
    
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute collect customer info.
        
        Args:
            request: Domain request with customer info in slots
            
        Returns:
            Domain response with collected info or missing fields
        """
        try:
            tenant_id = self._extract_tenant_id(request)
            
            # Extract customer info from slots
            name = request.slots.get("name") or request.slots.get("customer_name")
            email = request.slots.get("email") or request.slots.get("customer_email")
            phone = request.slots.get("phone") or request.slots.get("customer_phone") or request.slots.get("phone_number")
            address = request.slots.get("address") or request.slots.get("shipping_address")
            payment_method = request.slots.get("payment_method")
            notes = request.slots.get("notes") or request.slots.get("order_notes")
            
            # Get existing customer info from session (if any)
            existing_info = request.user_context.get("customer_info") or {}
            if isinstance(existing_info, dict):
                name = name or existing_info.get("name")
                email = email or existing_info.get("email")
                phone = phone or existing_info.get("phone")
                address = address or existing_info.get("address")
                payment_method = payment_method or existing_info.get("payment_method")
                notes = notes or existing_info.get("notes")
            
            # Check what's missing
            missing_fields = []
            if not name or not name.strip():
                missing_fields.append("name")
            if not email or not email.strip():
                missing_fields.append("email")
            if not phone or not phone.strip():
                missing_fields.append("phone")
            if not address or not address.strip():
                missing_fields.append("address")
            
            # Validate email format if provided
            if email and email.strip():
                if not self._validate_email(email.strip()):
                    return DomainResponse(
                        status=DomainResult.INVALID_REQUEST,
                        message="Email không hợp lệ. Vui lòng nhập lại email.",
                        error_code="INVALID_EMAIL",
                        missing_slots=["email"]
                    )
            
            # Validate phone format if provided
            if phone and phone.strip():
                if not self._validate_phone(phone.strip()):
                    return DomainResponse(
                        status=DomainResult.INVALID_REQUEST,
                        message="Số điện thoại không hợp lệ. Vui lòng nhập lại số điện thoại.",
                        error_code="INVALID_PHONE",
                        missing_slots=["phone"]
                    )
            
            logger.info(
                "Collecting customer info",
                extra={
                    "trace_id": request.trace_id,
                    "tenant_id": tenant_id,
                    "has_name": bool(name),
                    "has_email": bool(email),
                    "has_phone": bool(phone),
                    "has_address": bool(address),
                    "missing_fields": missing_fields,
                }
            )
            
            # If missing fields, ask for them
            if missing_fields:
                field_names = {
                    "name": "tên",
                    "email": "email",
                    "phone": "số điện thoại",
                    "address": "địa chỉ giao hàng"
                }
                
                if len(missing_fields) == 1:
                    field_name = field_names.get(missing_fields[0], missing_fields[0])
                    message = f"Vui lòng cung cấp {field_name} của bạn."
                else:
                    missing_list = [field_names.get(f, f) for f in missing_fields]
                    message = f"Vui lòng cung cấp: {', '.join(missing_list)}."
                
                return DomainResponse(
                    status=DomainResult.NEED_MORE_INFO,
                    message=message,
                    missing_slots=missing_fields,
                    next_action="ASK_SLOT",
                    next_action_params={
                        "slot_name": missing_fields[0],
                        "all_missing": missing_fields
                    },
                    data={
                        "collected_info": {
                            "name": name,
                            "email": email,
                            "phone": phone,
                            "address": address,
                            "payment_method": payment_method,
                            "notes": notes,
                        },
                        "missing_fields": missing_fields
                    }
                )
            
            # All fields collected, validate and format
            customer_info = {
                "name": name.strip(),
                "email": email.strip().lower(),
                "phone": self._normalize_phone(phone.strip()),
                "address": address.strip(),
                "payment_method": payment_method.strip() if payment_method else None,
                "notes": notes.strip() if notes else None,
            }
            
            return DomainResponse(
                status=DomainResult.SUCCESS,
                message=f"Cảm ơn bạn, {customer_info['name']}! Thông tin của bạn đã được lưu. Bạn có muốn tiếp tục đặt hàng không?",
                data={
                    "customer_info": customer_info,
                    "all_fields_collected": True
                },
                audit={
                    "intent": request.intent,
                    "customer_name": customer_info["name"],
                    "customer_email": customer_info["email"],
                    "has_payment_method": bool(customer_info["payment_method"]),
                }
            )
            
        except Exception as e:
            logger.error(
                f"Collect customer info use case error: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi thu thập thông tin. Vui lòng thử lại sau.",
                error_code="COLLECT_INFO_ERROR"
            )
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone format (Vietnamese phone numbers)"""
        # Remove spaces, dashes, parentheses
        phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
        # Check if it's all digits (with optional + prefix)
        if phone_clean.startswith('+'):
            digits = phone_clean[1:]
        else:
            digits = phone_clean
        # Vietnamese phone: 10 digits (0xx...) or 11 digits (84xx...)
        return digits.isdigit() and len(digits) >= 9 and len(digits) <= 11
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove spaces, dashes, parentheses
        phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
        # Add +84 prefix if starts with 0
        if phone_clean.startswith('0'):
            phone_clean = '+84' + phone_clean[1:]
        elif not phone_clean.startswith('+'):
            phone_clean = '+84' + phone_clean
        return phone_clean
