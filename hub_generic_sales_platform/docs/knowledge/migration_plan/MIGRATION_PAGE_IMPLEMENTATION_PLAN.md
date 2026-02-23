# Kế hoạch triển khai trang Migration Data

**Mục tiêu**: Xây dựng trang `/migration` để migrate dữ liệu từ nhiều nguồn (Web Scraper, Excel, v.v.) vào Catalog và Knowledge Base, dựa trên kiến trúc hiện có và design tokens của Catalog/Knowledge.

---

## 1. Phân tích nguồn tham chiếu

### 1.1 Page Catalog (`/catalog`)

| Yếu tố | Chi tiết |
|--------|----------|
| **Layout** | Header + Stats + BotSelector + Split view (List trái | Detail phải) |
| **Components** | `CatalogStats`, `BotSelector`, `OfferingList`, `OfferingDetail`, `GlassContainer` |
| **Data flow** | `apiService.listCatalogOfferings(channel, botId)` → CRUD qua mutations |
| **Design token** | `premium-gradient`, `bg-white/5`, `border-white/10`, `text-accent` |
| **Pattern** | Query → Filter → Selection → Mutations → `invalidateQueries` |

### 1.2 Page Knowledge (`/knowledge`)

| Yếu tố | Chi tiết |
|--------|----------|
| **Layout** | Header + Stats cards (4) + BotSelector + Tabbed content |
| **Tabs** | FAQs, Use Cases, Comparisons, Guardrails, Semantic Cache |
| **Design** | Stats grid, GlassContainer, tab button group, search bar |
| **Data** | FAQs, UseCases, Comparisons, Guardrails theo `effectiveDomainId` từ bot |

### 1.3 Scripts/Seed

- **`knowledge.py`**: Cấu trúc dữ liệu migrate:
  - `TenantOffering` → `TenantOfferingVersion` → `TenantOfferingAttributeValue`
  - `TenantOfferingVariant` → `TenantVariantPrice` → `TenantInventoryItem`
  - `BotFAQ`, `BotUseCase`, `BotComparison`, `TenantGuardrail`
- **`ontology.py`**: `DomainAttributeDefinition` theo domain (key → id mapping)
- **Schema output**: `code`, `name`, `description`, `variants[]`, `attributes{}`

### 1.4 Docs Migration Plan

- **migration_strategy.md**: Bulk Upsert, Identifier `code`/`sku`, Review before Commit (staging)
- **migration_checklist.md**: Table `migration_job`, API `scrape`/`jobs`/`confirm`
- **extensible_migration_arch.md**: Pluggable Provider, Unified Preview, Migration Center
- **ai_scraper_guide.md**: Playwright + LLM, JSON output chuẩn

### 1.5 Backend hiện có

| API | Method | Mô tả |
|-----|--------|-------|
| `POST /catalog/migrate/scrape` | JSON `{url, bot_id?, domain_id?}` | Bắt đầu cào → trả `job_id` |
| `GET /catalog/migrate/jobs` | - | List jobs tenant |
| `GET /catalog/migrate/jobs/{id}` | - | Chi tiết job + `staged_data` |
| `POST /catalog/migrate/jobs/{id}/confirm` | - | Commit vào Catalog |

**apiService** đã có: `startScrape`, `getMigrationJob`, `confirmMigration`, `listMigrationJobs`.

---

## 2. Kiến trúc trang Migration

### 2.1 Sơ đồ luồng

```
┌─────────────────────────────────────────────────────────────────────┐
│  MIGRATION PAGE                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  [Source Selection]  Web Scraper (MVP) | Excel (Phase 2)           │
│  [BotSelector]       Chọn Bot → domain_id                          │
│  [Input]             URL sản phẩm / Sitemap / Upload file           │
│  [Start]             POST /scrape → job_id                          │
├─────────────────────────────────────────────────────────────────────┤
│  [Job History]       Bảng danh sách jobs (pending/processing/staged)│
│  [Preview]           staged_data → Bảng sản phẩm inline editable   │
│  [Confirm]           POST /jobs/{id}/confirm → Success              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Cấu trúc thư mục

```
frontend/
├── app/
│   └── migration/
│       └── page.tsx              # Trang chính Migration
├── components/
│   └── migration/
│       ├── MigrationSourceSelector.tsx   # Chọn nguồn (Web/Excel)
│       ├── MigrationJobList.tsx          # Danh sách jobs
│       ├── MigrationPreviewTable.tsx     # Bảng preview staged
│       └── MigrationInputForm.tsx        # Form URL/Bot input
```

---

## 3. Chi tiết triển khai (theo phase)

### Phase 1: MVP - Web Scraper (1 trang)

**Mục tiêu**: Có thể nhập URL → Cào → Preview → Confirm.

#### 3.1.1 Tạo `app/migration/page.tsx`

| Section | Nội dung |
|---------|----------|
| **Header** | "Migration Center" + subtitle "Import dữ liệu từ Web, Excel" |
| **Stats** | Số jobs (Total, Staged, Completed, Failed) |
| **BotSelector** | Copy pattern từ Catalog/Knowledge (list bots, chọn bot) |
| **Input Form** | Input URL + Button "Bắt đầu cào" |
| **Job List** | Table: ID, URL, Status, Created | Actions: Xem Preview, Confirm |
| **Preview Modal** | Hiển thị `staged_data.offerings[]` dạng table, có nút Confirm |

**State & Queries**:
- `selectedBotId` → `domain_id` lấy từ bot
- `useQuery(["migration-jobs"], listMigrationJobs)`
- `useMutation(startScrape)` → invalidate jobs
- `useMutation(confirmMigration)` → invalidate jobs + catalog-offerings

#### 3.1.2 Design tokens (theo Catalog/Knowledge)

- `GlassContainer` cho các block
- `premium-gradient` cho nút chính
- `bg-white/5`, `border-white/10` cho form
- `text-accent` cho trạng thái active
- Status badge: `pending` (yellow), `processing` (blue), `staged` (green), `completed` (gray), `failed` (red)

#### 3.1.3 Thêm vào Navigation

```ts
// navConfig.ts - thêm vào group "DỮ LIỆU"
{
  icon: Database,  // hoặc Upload icon
  label: "Migration Data",
  href: "/migration",
}
```

**Icon gợi ý**: `Upload` hoặc `Database` từ lucide-react.

### Phase 2: Nâng cấp Preview & UX

| Hạng mục | Chi tiết |
|----------|----------|
| **Polling** | Khi job `processing`, poll `getMigrationJob` mỗi 2s đến khi `staged`/`failed` |
| **Inline Edit** | Trong Preview: sửa `name`, `price`, `code` trước khi Confirm (cần API PATCH staged?) |
| **Attribute Mapping** | UI map cột nguồn → `AttributeDefinition` (nếu backend hỗ trợ) |
| **Error Display** | Hiển thị `error_log` khi job `failed` |

### Phase 3: Excel Import (mở rộng)

- Upload file CSV/Excel
- Backend: `ExcelMigrationProvider` (BaseMigrationProvider)
- API: `POST /catalog/migrate/upload` → tạo job `source_type=excel_upload`
- Mapping UI: Chọn cột Excel → Schema Hub

### Phase 4: Knowledge Migration (FAQs, Use Cases)

- Nếu staged_data có `faqs[]`, `usecases[]` → Commit vào `BotFAQ`, `BotUseCase`
- Cần mở rộng `MigrationService.commit_job` hỗ trợ knowledge entities

---

## 4. Checklist triển khai Phase 1

### Backend (đã sẵn sàng)

- [x] `POST /catalog/migrate/scrape`
- [x] `GET /catalog/migrate/jobs`
- [x] `GET /catalog/migrate/jobs/{id}`
- [x] `POST /catalog/migrate/jobs/{id}/confirm`
- [x] apiService methods

### Frontend

- [ ] Tạo `frontend/app/migration/page.tsx`
- [ ] Thêm nav item "Migration Data" vào `navConfig.ts`
- [ ] Component `MigrationInputForm`: URL + Bot + Start
- [ ] Component `MigrationJobList`: Table jobs + status
- [ ] Component `MigrationPreviewModal`: staged_data table + Confirm
- [ ] Polling khi job `processing`
- [ ] Toast success/error cho mutations

### Testing

- [ ] Manual: Nhập URL Tiki/Shopee → Verify staged_data → Confirm → Kiểm tra Catalog
- [ ] Kiểm tra tenant isolation

---

## 5. Schema staged_data (tham chiếu)

Theo `migration_service.commit_job` và `ai_scraper_guide.md`:

```json
{
  "offerings": [
    {
      "code": "PROD-XXX",
      "name": "Tên sản phẩm",
      "description": "Mô tả",
      "attributes": {
        "screen_size": "6.1 inch",
        "chip": "A17 Pro"
      },
      "variants": [
        { "sku": "SKU-001", "name": "Màu Titan", "price": 28990000 },
        { "sku": "SKU-002", "name": "Màu Xanh", "price": 28990000 }
      ]
    }
  ]
}
```

---

## 6. Thứ tự thực hiện đề xuất

1. **Bước 1**: Tạo `app/migration/page.tsx` cơ bản (form + job list + preview modal)
2. **Bước 2**: Thêm nav item
3. **Bước 3**: Tích hợp polling cho job processing
4. **Bước 4**: Refactor thành components (MigrationInputForm, MigrationJobList, MigrationPreviewTable)
5. **Bước 5**: Polish UX (loading, error states, empty states)

---

## 7. Ràng buộc & lưu ý

- **Tenant isolation**: Mọi API đã có `get_current_tenant_id`
- **Domain_id bắt buộc**: Scrape cần `domain_id` (từ bot hoặc truyền trực tiếp)
- **Không đổi schema DB**: Sử dụng `migration_job` hiện có
- **Design tokens**: Tuân thủ `.cursor/rules` và pattern Catalog/Knowledge
