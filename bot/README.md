# Hub Bot - Global Router System

Hệ thống routing thông minh với kiến trúc 3 tầng tách biệt: Interface Layer → Global Router → Domain Engines.

## 🏗️ Kiến trúc

```
Interface Layer
    ↓
Global Router (Decision System)
    ↓
Domain Engines (Business Systems)
```

- **Router**: Chỉ làm quyết định routing, không làm nghiệp vụ
- **Domain**: Chỉ xử lý nghiệp vụ, không tự route
- **Interface**: Chỉ nhận input/output, không biết logic

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Redis
- PostgreSQL

### 2. Setup

```bash
# Clone repository
git clone <repo-url>
cd hub

# Copy environment file
cp env.example .env

# Edit .env với các giá trị thực tế
# - OPENAI_API_KEY (hoặc ANTHROPIC_API_KEY)
# - SECRET_KEY
# - Database credentials

# Start infrastructure
docker-compose up -d

# Install dependencies
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Run application
python scripts/startup.py
# hoặc
uvicorn interface.api:app --reload
```

### 3. Verify

```bash
# Health check
curl http://localhost:8386/health

# Test routing
curl -X POST http://localhost:8386/api/v1/router/route \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tôi còn bao nhiêu ngày phép?",
    "user_id": "test-user-123"
  }'
```

## 📁 Cấu trúc Project

```
bot/
├── backend/
│   ├── router/              # Router Orchestrator
│   │   ├── orchestrator.py   # Main router
│   │   └── steps/            # Routing steps (0-6)
│   ├── domain/               # Domain Engines
│   │   └── hr/               # HR Domain (example)
│   ├── knowledge/            # Knowledge Engines (RAG)
│   ├── personalization/      # Personalization module
│   ├── interface/            # Interface Layer (API)
│   ├── types/                # Type definitions
│   └── shared/               # Shared support
├── config/
│   └── intent_registry.yaml  # Intent registry
├── tests/                    # Test suite
├── docker-compose.yml        # Docker services
└── requirements.txt          # Dependencies
```

## 🔧 Development

### Code Style

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make type-check
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=backend --cov-report=html
```

## 📊 Monitoring

- **API**: http://localhost:8386
- **pgAdmin**: http://localhost:5050
- **Redis Insight**: http://localhost:8389
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## 📚 Documentation

- **Architecture**: `docs/rules_global_router/architecture.md`
- **Implementation Plan**: `docs/implementation_plan.md`
- **Progress Tracker**: `docs/progress_tracker.md`
- **Phase 1 Start**: `PHASE1_START.md`
- **Setup Guide**: `SETUP.md`
- **Personalization Guide**: `docs/personalization_guide.md`

## 🎯 Current Status

**Phase**: 1 - Foundation (Weeks 1-2)  
**Progress**: 0% - Setup complete, ready to start implementation

See `PHASE1_START.md` for next steps.

## 📝 License

Internal use only.
