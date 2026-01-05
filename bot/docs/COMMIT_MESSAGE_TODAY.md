# Commit Message - Use Case Discovery & Vietnamese Market Optimization

## Summary
- Tối ưu seed data cho thị trường Việt Nam
- Implement Use Case Discovery System
- Thêm Rule Name Suggestions từ Routing Rules
- Tích hợp Use Case Selector vào Pattern Rules form

## Changes

### Backend

#### 1. Seed Data Optimization (Vietnamese Market)
- **File**: `bot/backend/scripts/seed_admin_data.py`
- **Changes**:
  - Tăng từ 5 → 8 pattern rules (thêm HR tra cứu lương, Catalog tra cứu giá, Cảm ơn)
  - Tối ưu keyword hints với weights cao hơn cho từ khóa tiếng Việt
  - Tăng từ 3 → 5 routing rules
  - Tăng từ 4 → 7 prompt templates (tất cả bằng tiếng Việt)
  - Cải thiện patterns để match tốt hơn với tiếng Việt (thêm variants: anh/chị, nghỉ việc, làm đơn, etc.)

#### 2. Use Case Registry
- **File**: `bot/backend/domain/use_case_registry.py` (NEW)
- **Purpose**: Auto-discover use cases từ domain handlers
- **Features**:
  - Discover intents từ HR, Catalog, Knowledge, Meta domains
  - Provide display names và descriptions tiếng Việt
  - Singleton pattern với caching
  - Support filtering by domain

#### 3. Admin API Endpoints
- **File**: `bot/backend/interface/admin_api.py`
- **New Endpoints**:
  - `GET /admin/use-cases` - List all domains và intents
    - Query param: `?domain=hr` để filter
  - `GET /admin/routing-rules/suggestions` - Get routing rule suggestions
    - Dùng để suggest rule names khi tạo pattern/keyword rules

### Frontend

#### 4. Use Case List Component
- **File**: `bot/frontend/src/components/UseCaseList.tsx` (NEW)
- **Features**:
  - Hiển thị tất cả use cases với filter theo domain
  - Color-coded intent types (OPERATION, KNOWLEDGE, META)
  - Responsive grid layout
  - Hiển thị intent code, description, domain

#### 5. Use Case Selector Component
- **File**: `bot/frontend/src/components/UseCaseSelector.tsx` (NEW)
- **Features**:
  - Dropdown selector với search
  - Auto-fill `target_intent`, `target_domain`, `intent_type` khi chọn
  - Hiển thị metadata (domain, intent_type, description)
  - Filter theo domain và intent_type

#### 6. Rule Name Suggestions Component
- **File**: `bot/frontend/src/components/RuleNameSuggestions.tsx` (NEW)
- **Features**:
  - Suggest rule names từ existing routing rules
  - Filter theo `target_intent` và `target_domain`
  - Click để auto-fill rule name và related fields
  - Collapsible UI

#### 7. Service Updates
- **File**: `bot/frontend/src/services/admin-config.service.ts`
- **New Methods**:
  - `listUseCases(domain?)` - List use cases
  - `getRoutingRuleSuggestions()` - Get routing rule suggestions

#### 8. Dashboard Integration
- **File**: `bot/frontend/src/app/admin/dashboard/page.tsx`
- **Changes**:
  - Thêm section "Use Cases Có Sẵn" với UseCaseList component
  - Hiển thị tất cả use cases để admin có thể reference

#### 9. Pattern Rules Form Enhancement
- **File**: `bot/frontend/src/app/admin/patterns/new/page.tsx`
- **Changes**:
  - Thay text input bằng UseCaseSelector cho Target Intent field
  - Thêm RuleNameSuggestions cho Rule Name field
  - Auto-sync fields khi chọn use case hoặc suggestion

#### 10. Documentation
- **File**: `bot/docs/SEED_DATA_GUIDE.md`
- **Updates**:
  - Cập nhật với data mới (8 patterns, 7 prompts, etc.)
  - Thêm sample queries tiếng Việt
  - Cập nhật descriptions

## Benefits

1. **Vietnamese Market Ready**: Seed data tối ưu cho tiếng Việt
2. **Discoverability**: Frontend biết use cases có sẵn, không cần hardcode
3. **Consistency**: Rule names sync giữa routing rules và pattern/keyword rules
4. **UX Improvement**: Auto-fill và suggestions giảm lỗi khi tạo rules
5. **Maintainability**: Auto-discover use cases, không cần update manual

## Testing

- [x] Seed data script chạy thành công
- [x] Use Case Registry discover đúng các domains
- [x] API endpoints trả về đúng data
- [x] Frontend components render và hoạt động đúng
- [x] Auto-fill hoạt động khi chọn use case/suggestion

## Files Changed

### New Files
- `bot/backend/domain/use_case_registry.py`
- `bot/frontend/src/components/UseCaseList.tsx`
- `bot/frontend/src/components/UseCaseSelector.tsx`
- `bot/frontend/src/components/RuleNameSuggestions.tsx`
- `bot/docs/COMMIT_MESSAGE_TODAY.md`

### Modified Files
- `bot/backend/scripts/seed_admin_data.py`
- `bot/backend/interface/admin_api.py`
- `bot/frontend/src/services/admin-config.service.ts`
- `bot/frontend/src/app/admin/dashboard/page.tsx`
- `bot/frontend/src/app/admin/patterns/new/page.tsx`
- `bot/docs/SEED_DATA_GUIDE.md`

## Commit Message

```
feat: Add use case discovery system and optimize for Vietnamese market

Backend:
- Add UseCaseRegistry to auto-discover use cases from domain handlers
- Add GET /admin/use-cases endpoint to list available intents
- Add GET /admin/routing-rules/suggestions endpoint for rule name suggestions
- Optimize seed_admin_data.py for Vietnamese market:
  * Increase pattern rules: 5 → 8 (add salary query, price query, thank you)
  * Improve keyword hints with higher weights for Vietnamese keywords
  * Increase routing rules: 3 → 5
  * Increase prompt templates: 4 → 7 (all in Vietnamese)
  * Enhance patterns to better match Vietnamese variants

Frontend:
- Add UseCaseList component to display all available use cases
- Add UseCaseSelector dropdown component with search and auto-fill
- Add RuleNameSuggestions component to suggest rule names from routing rules
- Integrate UseCaseList into dashboard
- Enhance Pattern Rules form with UseCaseSelector and RuleNameSuggestions
- Update admin-config.service with new API methods

Benefits:
- Vietnamese market ready with optimized seed data
- Better discoverability of available use cases
- Improved UX with auto-fill and suggestions
- Consistency between routing rules and pattern/keyword rules
- Auto-discovery reduces manual maintenance

Files:
- New: use_case_registry.py, UseCaseList.tsx, UseCaseSelector.tsx, RuleNameSuggestions.tsx
- Modified: seed_admin_data.py, admin_api.py, admin-config.service.ts, dashboard/page.tsx, patterns/new/page.tsx, SEED_DATA_GUIDE.md
```

