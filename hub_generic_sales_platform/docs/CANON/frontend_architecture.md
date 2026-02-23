# Frontend Architecture: AI-Native Dashboard (Bot_v4)

Frontend được xây dựng dựa trên Next.js 16+, tập trung vào trải nghiệm **Premium**, **AI-Native**, và khả năng **Commercialization** (Thương mại hóa).

## 1. Cấu trúc Thư mục Chi tiết (Folder Responsibilities)

```text
frontend/
├── app/                     # NEXT.JS APP ROUTER (Pages & Layouts)
│   ├── (auth)/              # Nhóm các trang xác thực (Login, Signup).
│   ├── analytics/           # Trang phân tích dữ liệu, chi phí và hiệu suất.
│   ├── bots/                # Quản lý danh sách và cấu hình chung của các Bot.
│   ├── catalog/             # Quản lý danh mục Offering của từng Tenant.
│   ├── knowledge/           # Trung tâm quản lý tri thức (FAQ, Use Case, Comparison).
│   ├── migration/           # Công cụ import dữ liệu (Web Scraper, Excel sync).
│   ├── studio/              # Playground: Tinh chỉnh Prompt và thử nghiệm AI Tooling.
│   ├── [other pages]/       # Monitor, Logs, Channels, Tenants, Settings...
│   ├── layout.tsx           # Bố cục tổng thể (Sidebar, Navbar, Theme Providers).
│   └── page.tsx             # Dashboard chính: Tổng quan hệ thống.
├── components/              # ATOMIC DESIGN COMPONENTS
│   ├── admin/               # Các component đặc thù cho Dashboard (Visualizers, Analytics charts).
│   ├── chat/                # Các component Generative UI cho luồng hội thoại (BentoGrid, Messages, Widget).
│   ├── ui/                  # Các component UI cơ bản dùng chung (Button, Card, Input - Shadcn-like).
│   └── Sidebar.tsx          # Thanh điều hướng chính của hệ thống.
├── lib/                     # SHARED LOGIC & STATE
│   ├── apiService.ts        # Trung tâm giao tiếp với Backend (axios/fetch wrapper).
│   ├── store.ts             # Quản lý trạng thái toàn cục (Zustand).
│   └── utils.ts             # Các hàm tiện ích (Format currency, date, normalization).
├── public/                  # Static assets (Images, Icons, Fonts).
└── styles/                  # Global CSS & Tailwind configuration.
```

## 2. Danh sách các Trang hiện tại (Current Pages)

Hệ thống cung cấp đầy đủ các giao diện để quản lý hệ sinh thái Hybrid AI:

| Trang | Route | Chức năng chính |
| :--- | :--- | :--- |
| **Dashboard** | `/` | Tổng quan về phiên chat, chi phí và trạng thái hệ thống. |
| **Bot Management** | `/bots` | Tạo mới, chỉnh sửa và gán Domain cho Bot. |
| **Knowledge Base** | `/knowledge` | Quản lý FAQ, so sánh Offering và các tình huống sử dụng (Use Cases). |
| **Offering Catalog** | `/catalog` | Quản lý dữ liệu Offering, thuộc tính và tồn kho cho từng Tenant. |
| **AI Studio** | `/studio` | Môi trường thử nghiệm Prompt và test các Tool của Agent. |
| **Data Migration** | `/migration` | Theo dõi và thực hiện các Job cào dữ liệu hoặc import từ file. |
| **Analytics** | `/analytics` | Biểu đồ chi tiết về Token Usage, Latency và Cost-per-Session. |
| **Monitor & Logs** | `/monitor`, `/logs` | Theo dõi hội thoại thời gian thực và truy vết quá trình suy luận (Decision Tree). |
| **Settings** | `/settings` | Cấu hình hệ thống, Tenant isolation và quản lý User. |

## 3. Triết lý Phát triển Frontend

1.  **AI-Native First:** Giao diện được thiết kế để hiển thị luồng suy nghĩ của AI (Decision Visualizer) và kết quả sinh ra dưới dạng tương tác (Generative UI).
2.  **State Management:** Sử dụng **Zustand** kết hợp với **React Query** để đảm bảo dữ liệu luôn đồng bộ với backend mà không cần reload trang.
3.  **Responsive & Glassmorphism:** Đảm bảo hiển thị cao cấp trên mọi thiết bị với ngôn ngữ thiết kế mờ đục hiện đại.
4.  **Security:** Tích hợp sẵn `ProtectedRoute` và `AuthStore` để quản lý quyền truy cập theo vai trò (Role-based Access Control).
