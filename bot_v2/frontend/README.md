# Bot V2 Admin Dashboard

Frontend admin dashboard cho Bot V2 - Multi-tenant catalog chatbot service.

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **React Query** (@tanstack/react-query)
- **Axios** (API client)

## Cấu trúc Project

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── admin/             # Admin pages
│   │   └── tenants/       # Tenant management
│   │       └── [id]/      # Tenant detail pages
│   ├── layout.tsx         # Root layout
│   ├── globals.css        # Global styles
│   └── page.tsx           # Home page (redirect to /admin/tenants)
├── components/            # React components
│   ├── layout/           # Layout components
│   │   ├── sidebar.tsx   # Sidebar navigation
│   │   └── main-layout.tsx
│   └── providers.tsx     # React Query provider
├── lib/                  # Utilities
│   ├── api-client.ts     # Axios client wrapper
│   ├── api.ts            # API functions
│   ├── types.ts          # TypeScript types
│   └── utils.ts          # Utility functions
└── package.json
```

## Pages

### 1. Tenant Management
- `/admin/tenants` - Danh sách tenants

### 2. Tenant Detail Pages
- `/admin/tenants/[id]/channels` - Quản lý channels
- `/admin/tenants/[id]/catalog` - Quản lý catalog (products)
- `/admin/tenants/[id]/catalog/[productId]` - Chi tiết product (attributes, use cases, FAQs)
- `/admin/tenants/[id]/intents` - Quản lý intents & routing
- `/admin/tenants/[id]/intents/[intentId]` - Chi tiết intent (patterns, hints, actions)
- `/admin/tenants/[id]/migrations` - Quản lý migration jobs
- `/admin/tenants/[id]/logs` - Conversation logs
- `/admin/tenants/[id]/failed-queries` - Failed queries

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Tạo file `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8386/api/v1
```

### 3. Run Development Server

```bash
npm run dev
```

Frontend sẽ chạy tại `http://localhost:3000`

## Features

### ✅ Đã implement

- Tenant management (list view)
- Channel configuration (list view)
- Catalog management (list + detail view)
  - Products list với search
  - Product detail với attributes, use cases, FAQs
- Intent & Routing management (list + detail view)
  - Intents list với domain filter
  - Intent detail với patterns, hints, actions
- Migration management (list view với status filter)
- Observability
  - Conversation logs
  - Failed queries

### 🔄 Cần mở rộng (future)

- CRUD operations (create, update, delete)
- Form validation
- File upload cho migrations
- Real-time updates
- Pagination
- Advanced filters
- Export data

## API Integration

Frontend sử dụng React Query để quản lý data fetching và caching. Tất cả API calls được định nghĩa trong `lib/api.ts` và sử dụng `lib/api-client.ts` làm wrapper cho Axios.

### API Base URL

Mặc định: `http://localhost:8386/api/v1`

Có thể config qua environment variable `NEXT_PUBLIC_API_URL`.

### Authentication

API client tự động thêm Bearer token từ `localStorage.getItem('auth_token')` vào headers nếu có.

## Styling

Sử dụng Tailwind CSS với custom color scheme:

- Primary colors (gray scale)
- Status colors (green/red/blue cho success/error/info)
- Consistent spacing và typography

## Notes

- Frontend hiện tại chỉ hiển thị dữ liệu (read-only)
- Chưa có authentication UI
- Chưa có form validation
- Chưa có error boundaries
