# Kiến Trúc Frontend: AI-Native Dashboard (Bot_v4)

## Tổng Quan

Frontend được xây dựng trên **Next.js 16+**, tập trung vào trải nghiệm **Premium**, **AI-Native**, và khả năng **Thương mại hóa (Commercialization)**.

=> **Điểm linh hoạt ăn tiền:** Admin Dashboard không chỉ quản lý cấu hình mà còn **trực quan hóa luồng suy nghĩ của AI** (Decision Tree). Khách hàng doanh nghiệp thấy rõ "Bot đã chọn tier nào, vì sao" - tăng niềm tin và khả năng bán (Sales).

---

## Cấu Trúc Thư Mục

```text
frontend/
├── app/                     # NEXT.JS APP ROUTER (Pages & Layouts)
│   ├── (auth)/              # Nhóm trang xác thực (Login, Signup)
│   ├── analytics/           # Phân tích dữ liệu, chi phí, hiệu suất
│   ├── bots/                # Quản lý Bot và cấu hình
│   ├── catalog/             # Quản lý Offering theo Tenant
│   ├── knowledge/           # Tri thức (FAQ, Use Case, Comparison)
│   ├── migration/           # Import dữ liệu (Web Scraper, Excel)
│   ├── studio/              # Playground: Prompt + test Tool
│   ├── [other pages]/       # Monitor, Logs, Channels, Tenants, Settings
│   ├── layout.tsx           # Bố cục (Sidebar, Navbar, Theme)
│   └── page.tsx             # Dashboard chính
├── components/              # ATOMIC DESIGN
│   ├── admin/               # Visualizers, Analytics charts
│   ├── chat/                # Generative UI (BentoGrid, Messages, Widget)
│   ├── ui/                  # Button, Card, Input (Shadcn-like)
│   └── Sidebar.tsx          # Điều hướng chính
├── lib/
│   ├── apiService.ts        # Giao tiếp Backend
│   ├── store.ts             # Trạng thái toàn cục (Zustand)
│   └── utils.ts             # Tiện ích (format, date...)
├── public/                  # Static assets
└── styles/                  # Global CSS, Tailwind
```

---

## Danh Sách Trang

Hệ thống cung cấp đầy đủ giao diện quản lý Hybrid AI:

| Trang | Route | Chức năng chính |
|-------|-------|-----------------|
| **Dashboard** | `/` | Tổng quan phiên chat, chi phí, trạng thái |
| **Bot Management** | `/bots` | Tạo, sửa Bot và gán Domain |
| **Knowledge Base** | `/knowledge` | FAQ, so sánh Offering, Use Cases |
| **Offering Catalog** | `/catalog` | Offering, thuộc tính, tồn kho theo Tenant |
| **AI Studio** | `/studio` | Test Prompt và Tool của Agent |
| **Data Migration** | `/migration` | Job cào dữ liệu, import file |
| **Analytics** | `/analytics` | Token, Latency, Cost-per-Session |
| **Monitor & Logs** | `/monitor`, `/logs` | Hội thoại realtime, Decision Tree |
| **Settings** | `/settings` | Cấu hình, Tenant, User |

---

## Triết Lý Phát Triển

1. **AI-Native First:** Giao diện hiển thị luồng suy nghĩ AI (Decision Visualizer) và kết quả dạng tương tác (Generative UI - Bento Grid, bảng so sánh).
2. **State Management:** **Zustand** + **React Query** - dữ liệu đồng bộ backend không cần reload.
3. **Responsive & Glassmorphism:** Hiển thị cao cấp mọi thiết bị, ngôn ngữ thiết kế mờ đục.
4. **Security:** `ProtectedRoute`, `AuthStore`, quyền theo vai trò (RBAC).

---

**Trạng thái Tài liệu**: Phản ánh triển khai hiện tại.
**Cập nhật lần cuối**: Tháng 02/2026.
