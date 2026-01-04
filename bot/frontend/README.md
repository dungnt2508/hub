# Bot Admin Dashboard

Frontend dashboard cho quản lý cấu hình bot service.

## Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Query** - Data fetching & caching
- **Axios** - HTTP client
- **Lucide React** - Icons

## Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

Tạo file `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8386
```

## Features

- ✅ Authentication (JWT)
- ✅ Dashboard overview
- ✅ Pattern Rules CRUD
- ✅ Keyword Hints CRUD
- ✅ Routing Rules CRUD
- ✅ Prompt Templates CRUD
- ✅ Test Sandbox
- ✅ Audit Logs viewer
- ✅ Admin Users management

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── admin/             # Admin pages
│   │   ├── dashboard/     # Dashboard overview
│   │   ├── patterns/      # Pattern rules
│   │   ├── keywords/      # Keyword hints
│   │   ├── routing/       # Routing rules
│   │   ├── prompts/      # Prompt templates
│   │   ├── test-sandbox/ # Test sandbox
│   │   └── audit-logs/   # Audit logs
│   └── login/             # Login page
├── components/           # React components
│   └── AdminLayout.tsx    # Main layout with sidebar
├── services/               # API services
│   └── admin-config.service.ts
└── shared/                 # Shared utilities
    ├── api/               # API client
    └── providers/         # React providers
```

## Development

Dashboard chạy trên port **3002** (khác với catalog frontend port 3000).

Truy cập: http://localhost:3002

