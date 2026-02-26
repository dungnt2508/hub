# Nền Tảng Bán Hàng Đa Năng (Generic Sales Platform)

> **Agentic Sales Platform** — Hệ thống Sales Bot thông minh cho Thương mại điện tử & Dịch vụ
>
> *Rẻ - Nhanh - Khôn*

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen)
![Python](https://img.shields.io/badge/Backend-FastAPI_Async-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js_16-black)
![Database](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-336791)
![AI](https://img.shields.io/badge/AI-Hybrid_Orchestrator-orange)

---

## Tổng quan

**Agentic Sales Platform** không chỉ là chatbot bán hàng thông thường. Đây là **Nền tảng Bán hàng Đa năng (Generic Sales Platform)** thiết kế linh hoạt cho mọi quy trình chuyển đổi — từ bán lẻ đơn giản đến dịch vụ giá trị cao (bất động sản, ô tô, tài chính).

=> **Điểm linh hoạt ăn tiền:** Hệ thống áp dụng mô hình **Offering-Centric** — không bắt buộc SKU hay giỏ hàng cố định. Nạp cấu hình ontology mới là Bot tự hiểu sản phẩm, không cần sửa code.

### Ba trụ cột

| Trụ | Mô tả |
|-----|-------|
| **Rẻ** | Kiến trúc Hybrid 3 tầng giảm ~50–70% chi phí LLM so với chatbot gọi AI mọi câu |
| **Nhanh** | Fast Path < 50ms, Knowledge Path < 500ms |
| **Khôn** | Agentic Reasoning + State Machine — Bot suy luận đa bước, chọn Tool theo trạng thái |

---

## Tài liệu hệ thống

### Bắt đầu

- [ROADMAP](docs/CANON/ROADMAP.md) — Kế hoạch phát triển

### Kiến trúc lõi

- [Generic Sales Platform](docs/CANON/generic_sales_platform.md) — Mô hình Offering-Centric, Context Slots, Lifecycle States
- [Backend Architecture](docs/CANON/backend_architecture.md) — Clean Architecture, 3-tier, State Machine
- [Frontend Architecture](docs/CANON/frontend_architecture.md) — Next.js App Router, Generative UI
- [System Flow](docs/CANON/SYSTEM_FLOW.md) — Luồng xử lý end-to-end
- [Runtime Flow](docs/CANON/runtime_flow.md) — Luồng dữ liệu runtime, bảng `runtime_*`
- [State Machine Guide](docs/CANON/STATE_MACHINE_GUIDE.md) — 13 trạng thái vòng đời, Tool scoping

### Schema & Logic

- [Database Schema](docs/CANON/SCHEMA_DB.MD) — Thiết kế đa tenant
- [Domain Model](docs/knowledge/domain/about_domain.md) — Entity và logic nghiệp vụ

### Thiết kế & Phát triển

- [Frontend Design](docs/CANON/frontend_design.md) — Nguyên tắc G-UI, Glassmorphism
- [Page Features](docs/knowledge/pages/PAGE_FEATURES.md) — Chức năng từng trang
- [Architectural Review](docs/CANON/architectural_review.md) — Đánh giá kiến trúc

### Bảo mật & Auth

- [Authentication Proposal](docs/knowledge/authentication_proposal.md) — Đề xuất JWT-based

### Báo cáo & Kế hoạch

- [Comprehensive Runtime Audit](docs/knowledge/report/comprehensive_runtime_audit.md)
- [Feasibility Report](docs/knowledge/report/feasibility_report.md)
- [Runtime Fix Plan](docs/knowledge/report/runtime_fix_plan.md)

### Migration & Scenarios

- [Migration Strategy](docs/knowledge/migration_plan/migration_strategy.md)
- [AI Scraper Guide](docs/knowledge/migration_plan/ai_scraper_guide.md)
- Scenarios: [Finance](docs/knowledge/scenarios/finance_unsecured_loan.md) · [Real Estate](docs/knowledge/scenarios/high_ticket_real_estate.md) · [Automotive](docs/knowledge/scenarios/used_car_sales.md) · [Education](docs/knowledge/scenarios/education_admissions.md)

### Khác

- [QA](docs/knowledge/QA.md) · [Tech Debt](docs/NOTE/tech_debt_analysis.md)

---

## Tech Stack

| Thành phần | Công nghệ |
|------------|-----------|
| **Backend** | Python, FastAPI | 100% Async, Clean Architecture |
| **Frontend** | Next.js 16, React | Server Components, Zustand, TailwindCSS |
| **Database** | PostgreSQL | pgvector (Embedding), SQLAlchemy 2.0 |
| **AI/LLM** | OpenAI, Gemini | Function Calling |
| **Infra** | Docker | Containerized |

---

## Quick Start

### Yêu cầu

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+

### Cài đặt

**1. Backend**

```bash
# Kích hoạt môi trường Python (vd: Env3_12)
# Windows PowerShell:
G:\project python\Env3_12\Scripts\activate

cd hub_generic_sales_platform   # hoặc thư mục project
pip install -r requirements.txt

# Cấu hình
cp example_env .env
# Chỉnh .env với API Key

# Migration
alembic upgrade head

# Chạy
uvicorn app.main:app --reload
```

**2. Frontend**

```bash
cd frontend
npm install
npm run dev
```

---

## Cấu trúc dự án

```text
hub_generic_sales_platform/
├── app/                    # Backend
│   ├── core/               # Domain (Entities, State Machine)
│   ├── application/        # Use Cases (Orchestrators, Handlers)
│   ├── infrastructure/     # DB, LLM, Search
│   └── interfaces/        # API, Middleware
├── frontend/               # Next.js
├── docs/
│   ├── CANON/              # Tài liệu chuẩn (Architecture, Flow)
│   ├── knowledge/          # Domain, Scenarios, Reports
│   └── NOTE/               # Tech Debt, Notes
├── scripts/
└── tests/
```

---

## Tính năng chính

### 1. Hybrid Intelligence Engine

- **Tier 1 (Fast Path):** Chào hỏi, social chit-chat → < 50ms, cost $0
- **Tier 2 (Knowledge Path):** Semantic search FAQ, Use Case → < 500ms
- **Tier 3 (Agentic Path):** LLM + Tools, suy luận đa bước

### 2. Offering-Centric Catalog

- Biến thể (Màu, Size, Phiên bản)
- Tồn kho (Inventory)
- Dynamic Pricing theo kênh, hạng khách

### 3. Lifecycle State Machine

13 trạng thái (IDLE → BROWSING → VIEWING → COMPARING → ANALYZING → PURCHASING...). Mỗi trạng thái có whitelist Tool riêng — Bot không "ngu", không gọi Tool sai ngữ cảnh.

### 4. Audit Trail

Mọi quyết định AI ghi vào `runtime_decision_event` — tier nào, lý do, cost, latency. Admin truy vết dễ dàng.

### 5. Generative UI (G-UI)

- Bento Grid — danh sách sản phẩm
- Comparison Table — so sánh thông số
- Charts — biến động giá (tài chính, BĐS)

---

## Đóng góp

Dự án tuân theo **Clean Code**. Đóng góp được chào đón!

---

> **Cập nhật**: Tháng 02/2026 · **Trạng thái**: Phản ánh triển khai hiện tại
