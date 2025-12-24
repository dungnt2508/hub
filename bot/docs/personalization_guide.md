# Personalization Guide

## Tổng quan

Tính năng cá nhân hóa cho phép user tùy chỉnh:
- **Avatar**: Emoji, URL, tên bot
- **Tông giọng**: Formal, Friendly, Professional, Casual, Humorous
- **Ngữ điệu**: Concise, Detailed, Conversational, Technical
- **API cá nhân**: Custom endpoints, headers, format

## Kiến trúc

Personalization được implement ở **Interface Layer**, không ảnh hưởng đến Router hay Domain logic.

```
User Request
    ↓
Interface Layer (APIHandler)
    ├─ Load User Preferences
    ├─ Call Router
    └─ Format Response (apply personalization)
    ↓
Formatted Response (with avatar, tone, style)
```

## Cấu trúc Code

```
backend/personalization/
├── __init__.py
├── types.py              # Tone, Style, AvatarConfig, UserPreferences
├── user_preferences.py   # PersonalizationService
└── response_formatter.py # ResponseFormatter

backend/interface/
├── __init__.py
└── api_handler.py        # APIHandler (applies personalization)
```

## Sử dụng

### 1. Set User Preferences

```python
from backend.personalization import PersonalizationService, Tone, Style, AvatarConfig

service = PersonalizationService()

# Set preferences
preferences = await service.update_preferences(
    user_id="user123",
    tone=Tone.FRIENDLY,
    style=Style.CONVERSATIONAL,
    avatar={
        "avatar_emoji": "😊",
        "custom_name": "Trợ lý ảo",
    }
)
```

### 2. Get User Preferences

```python
preferences = await service.get_preferences("user123")
print(preferences.tone)  # Tone.FRIENDLY
print(preferences.style)  # Style.CONVERSATIONAL
```

### 3. Use in API Handler

```python
from backend.interface import APIHandler

handler = APIHandler()

# Personalization tự động được apply
response = await handler.handle_request(
    raw_message="Tôi còn bao nhiêu ngày phép?",
    user_id="user123",
)

# Response includes:
# - message: formatted với tone/style
# - avatar: emoji, url, name
# - metadata: tone, style
```

## Tone Options

- **FORMAL**: Trang trọng ("quý khách", "chúng tôi")
- **FRIENDLY**: Thân thiện (mặc định)
- **PROFESSIONAL**: Chuyên nghiệp
- **CASUAL**: Thân mật ("bạn", "mình")
- **HUMOROUS**: Hài hước (thêm emoji nhẹ)

## Style Options

- **CONCISE**: Ngắn gọn, bỏ filler words
- **DETAILED**: Chi tiết, thêm context
- **CONVERSATIONAL**: Trò chuyện (mặc định)
- **TECHNICAL**: Kỹ thuật, chính xác

## Avatar Configuration

```python
avatar = AvatarConfig(
    avatar_id="avatar_123",
    avatar_url="https://example.com/avatar.png",
    avatar_emoji="😊",  # Fallback
    custom_name="Trợ lý ảo",
)
```

## API Preferences

```python
api_prefs = APIPreferences(
    custom_endpoints={
        "hr": "https://custom-hr-api.com",
    },
    custom_headers={
        "X-Custom-Header": "value",
    },
    response_format="json",
    timeout_seconds=30,
)
```

## Response Format

Response từ API Handler bao gồm:

```json
{
  "message": "Bạn còn 7 ngày phép",
  "domain": "hr",
  "intent": "query_leave_balance",
  "status": "ROUTED",
  "trace_id": "uuid",
  "avatar": {
    "emoji": "😊",
    "url": "https://example.com/avatar.png",
    "name": "Trợ lý ảo"
  },
  "metadata": {
    "tone": "friendly",
    "style": "conversational"
  }
}
```

## Lưu trữ Preferences

Preferences được lưu per-user (không phải per-session), trong database hoặc cache.

### TODO: Implement Repository

```python
# backend/personalization/repository.py
class PreferencesRepository:
    async def get(self, user_id: str) -> Optional[UserPreferences]:
        # Load from database
        pass
    
    async def save(self, preferences: UserPreferences) -> UserPreferences:
        # Save to database
        pass
```

## Best Practices

1. **Default Preferences**: Luôn có default nếu user chưa set
2. **Validation**: Validate tone/style values
3. **Caching**: Cache preferences để tránh DB calls
4. **Fallback**: Nếu load preferences fail, dùng default
5. **Performance**: Load preferences async, không block request

## Testing

```python
# Test personalization
async def test_personalization():
    service = PersonalizationService()
    
    # Set preferences
    prefs = await service.update_preferences(
        user_id="test",
        tone=Tone.FORMAL,
    )
    
    # Verify
    assert prefs.tone == Tone.FORMAL
    
    # Test formatter
    formatter = ResponseFormatter(service)
    formatted = await formatter.format_router_response(
        router_response,
        "test"
    )
    
    assert "quý khách" in formatted["message"]  # Formal tone
```

