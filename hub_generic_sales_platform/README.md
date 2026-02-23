# Agentic Sales Platform 2026

> **Hệ thống Sales Bot thông minh cho Thương mại điện tử & Dịch vụ**
>
> *Rẻ - Nhanh - Khôn*

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen)
![Python](https://img.shields.io/badge/Backend-FastAPI_Async-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js_16-black)
![Database](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-336791)
![AI](https://img.shields.io/badge/AI-Hybrid_Orchestrator-orange)

---

## Tổng quan

**Agentic Sales Platform** là nền tảng AI Sales Orchestration thế hệ mới, được thiết kế để tự động hóa toàn bộ quy trình bán hàng - từ tư vấn, so sánh đến chốt đơn.

### Điểm khác biệt chính
- **Rẻ**: Kiến trúc Hybrid 3 tầng tối ưu chi phí gọi LLM xuống **90%** so với chatbot thông thường
- **Nhanh**: Fast Path xử lý tức thì < 50ms, Knowledge Path < 500ms
- **Khôn**: Agentic Reasoning cho phép bot suy luận đa bước, tự chọn công cụ phù hợp

---

## Tài liệu hệ thống

### Bắt đầu nhanh
- [Roadmap](docs/CANON/ROADMAP.md) - Kế hoạch phát triển & chiến lược

### Kiến trúc
- [Backend Architecture](docs/CANON/backend_architecture.md) - Kiến trúc Clean Architecture + Async
- [Frontend Architecture](docs/CANON/frontend_architecture.md) - Next.js App Router & Component Design
- [Database Schema](docs/CANON/SCHEMA_DB.MD) - Thiết kế Schema đa tenant
- [System Flow](docs/CANON/SYSTEM_FLOW.md) - Luồng xử lý dữ liệu end-to-end
- [Architectural Review](docs/CANON/architectural_review.md) - Đánh giá kiến trúc tổng thể

### Domain & Logic
- [Generic Sales Platform](docs/CANON/generic_sales_platform.md) - Giải thích mô hình Offering-Centric
- [Domain Model](docs/CANON/domain/about_domain.md) - Domain Entities & Business Logic
- [State Machine Guide](docs/CANON/pages/state_machine/STATE_MACHINE_GUIDE.md) - Cách hoạt động của State Machine
- [Runtime Flow](docs/CANON/runtime_flow/flow.md) - Luồng xử lý runtime chi tiết

### Bảo mật & Xác thực
- [Authentication Proposal](docs/CANON/authentication_proposal.md) - Đề xuất hệ thống Auth JWT-based

### Giao diện & UX
- [Frontend Design](docs/CANON/frontend_design.md) - Nguyên tắc thiết kế UI/UX
- [Page Features](docs/CANON/pages/PAGE_FEATURES.md) - Chức năng từng trang
- [Development Priority](docs/CANON/pages/DEVELOPMENT_PRIORITY.md) - Độ ưu tiên phát triển

### Audit & Báo cáo
- [Comprehensive Runtime Audit](docs/CANON/report/comprehensive_runtime_audit.md) - Audit chi tiết logic runtime
- [Feasibility Report](docs/CANON/report/feasibility_report.md) - Đánh giá tính khả thi thương mại
- [Runtime Fix Plan](docs/CANON/report/runtime_fix_plan.md) - Kế hoạch sửa các lỗi runtime
- [Walkthrough](docs/CANON/report/walkthrough.md) - Hướng dẫn kiểm thử sau fix

### Migration & Scraping
- [Migration Strategy](docs/CANON/migration_plan/migration_strategy.md) - Chiến lược di chuyển dữ liệu
- [AI Scraper Guide](docs/CANON/migration_plan/ai_scraper_guide.md) - Hướng dẫn sử dụng AI Scraper
- [Real Scraper Plan](docs/CANON/migration_plan/real_scraper_plan.md) - Kế hoạch scraper thực tế

### Use Cases / Scenarios
- [Finance - Unsecured Loan](docs/CANON/scenarios/finance_unsecured_loan.md)
- [Real Estate - High Ticket](docs/CANON/scenarios/high_ticket_real_estate.md)
- [Automotive - Used Car Sales](docs/CANON/scenarios/used_car_sales.md)
- [Education - Admissions](docs/CANON/scenarios/education_admissions.md)

### Q&A & Tech Debt
- [QA Documentation](docs/CANON/QA.md) - Câu hỏi thường gặp
- [Tech Debt Analysis](docs/NOTE/tech_debt_analysis.md) - Phân tích nợ kỹ thuật

---

## Tech Stack

| Component | Technology | Highlights |
| :--- | :--- | :--- |
| **Backend** | Python, FastAPI | 100% Async, Clean Architecture (DDD) |
| **Frontend** | Next.js 16, React | Server Components, Zustand, TailwindCSS v4 |
| **Database** | PostgreSQL | `pgvector` for Embedding, SQLAlchemy 2.0 |
| **AI LLM** | OpenAI / Gemini | Function Calling, Structured Output |
| **Infra** | Docker | Containerized, Scalable |

---

## Quick Start

### Yêu cầu
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+

### Cài đặt (Local Dev)

**1. Backend**
```bash
cd bot_v4
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Cấu hình .env
cp example_env .env
# Chỉnh sửa .env với API Key của bạn

# Database Migration
alembic upgrade head

# Start Server
uvicorn app.main:app --reload
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```text
bot_v4/
├── app/                  # Backend Core
│   ├── core/             # Business Logic & Entities (Pure Python)
│   ├── application/      # Use Cases & Orchestrators
│   ├── infrastructure/   # DB Adapter, LLM Provider
│   └── interfaces/       # API & Webhooks
├── frontend/             # Next.js Application
├── docs/                 # Documentation (Architecture, Guides)
│   ├── CANON/            # Core documentation & specifications
│   └── NOTE/             # Technical notes & analysis
├── scripts/              # Utility Scripts
└── tests/                # Unit & Integration Tests
```

---

## Tính năng nổi bật

### 1. Hybrid Intelligence Engine
Phân loại luồng thông minh:
- **Tier 1 (Fast Path)**: Xử lý chào hỏi, social chit-chat -> **Latency < 50ms**
- **Tier 2 (Knowledge Path)**: Semantic Search cho FAQ & Policy -> **Latency < 500ms**
- **Tier 3 (Agentic Path)**: Dùng LLM (GPT-4o/Gemini) để tư duy, so sánh sản phẩm, chốt đơn

### 2. Offering-Centric Catalog
- Quản lý **Biến thể** (Màu sắc, Size, Phiên bản)
- Kiểm soát **Tồn kho** thực tế (Inventory Aware)
- **Dynamic Pricing**: Giá hiển thị theo kênh bán (Zalo, Web) và hạng khách hàng

### 3. Decision Engine & Guardrails
- **Cost Control**: Tính toán chi phí $ trước khi trả lời
- **Safety**: Chặn các câu hỏi nhạy cảm, competitor attack
- **Audit Trail**: Ghi log chi tiết lý do ra quyết định của AI

### 4. Generative UI (G-UI)
Vẽ giao diện ngay trong khung chat:
- **Bento Grid**: Hiển thị bộ sưu tập sản phẩm
- **Comparison Table**: Bảng so sánh thông số kỹ thuật
- **Charts**: Biểu đồ biến động giá (cho tài chính/bất động sản)

---

## Đóng góp

Dự án được phát triển với tiêu chuẩn **Clean Code**. Mọi đóng góp đều được chào đón!

---

> **Develop by gsnake team**
