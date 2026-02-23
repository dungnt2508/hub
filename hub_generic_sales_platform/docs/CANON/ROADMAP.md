# Project Roadmap 2026

## Vision

**Agentic Sales Platform** là hệ thống AI Sales Orchestration thế hệ mới, được thiết kế với triết lý "Rẻ - Nhanh - Khôn" thông qua kiến trúc Hybrid 3-Tier Processing.

## Current State (As of Feb 2026)

### Architecture Foundation ✅ 
- **Clean Architecture**: Hexagonal Architecture với 4 layers (Core, Application, Infrastructure, Interfaces)
- **100% Async**: Toàn bộ database operations và API endpoints sử dụng async/await
- **Multi-tenant**: Row-level security với `tenant_id` isolation
- **PostgreSQL + pgvector**: Vector search cho semantic matching

### Hybrid Orchestration ✅
**HybridOrchestrator** điều phối 3 tầng xử lý:

1. **Tier 1 - Fast Path** (Latency < 50ms, Cost: $0)
   - Pattern matching cho social chit-chat
   - Regex-based instant responses
   - Zero LLM calls

2. **Tier 2 - Knowledge Path** (Latency < 500ms, Cost: Mini)
   - Semantic cache lookup
   - FAQ vector search (pgvector)
   - Confidence-based auto-response (threshold > 0.85)

3. **Tier 3 - Agentic Path** (High intelligence, Cost: Variable)
   - **AgentOrchestrator** với reasoning loop
   - Conversation history injection
   - Context slots injection vào system prompt
   - Tool-based execution (search, compare, details)
   - State machine constraints

### Intelligence Enhancements ✅
- **History Injection**: LLM nhận đầy đủ conversation history để hiểu ngữ cảnh
- **Context Slots**: Slot filling và injection vào system prompt
- **Smart Tool Fallback**: Tools tự động sử dụng context slots khi thiếu arguments
- **Relaxed State Machine**: Flexible tool access dựa trên lifecycle state

### Catalog Management ✅
- **Offering-Centric Model**: Hỗ trợ Products, Services, Assets
- **Dynamic Attributes**: JSONB-based attributes theo domain
- **Variant Management**: Colors, sizes, versions
- **Inventory Tracking**: Real-time stock levels
- **Dynamic Pricing**: Channel-based và customer segment pricing

## Next Phase: Production Readiness

### Sprint 3: Integration & Channels (6-8 weeks)
**Goal**: Multi-channel deployment và production infrastructure

#### 3.1 Multi-Channel Integration
- [ ] Zalo OA Webhook Integration
  - Message handling
  - Rich message formatting
  - Authentication flow
- [ ] Facebook Messenger Integration
  - Graph API integration
  - Message templates
  - User profile sync
- [ ] Web Widget SDK
  - Embeddable chat widget
  - Customizable themes
  - Event tracking

#### 3.2 Production Infrastructure
- [ ] Redis Cache Layer
  - Semantic cache storage
  - Session state caching
  - Rate limiting
- [ ] Message Queue (RabbitMQ/SQS)
  - Async job processing
  - Retry mechanisms
  - Dead letter queue
- [ ] Monitoring & Observability
  - Prometheus metrics
  - Grafana dashboards
  - Cost tracking per session

#### 3.3 Advanced Features
- [ ] LLM Provider Switching
  - Multi-provider support (OpenAI, Gemini, Claude)
  - Automatic fallback
  - Cost optimization per use case
- [ ] A/B Testing Framework
  - System prompt variations
  - Flow path experiments
  - Conversion tracking

### Sprint 4: Enterprise Features (8-10 weeks)
**Goal**: Enterprise-grade capabilities

#### 4.1 Security & Compliance
- [ ] Role-based Access Control (RBAC)
- [ ] Audit logging cho compliance
- [ ] Data encryption at rest
- [ ] GDPR compliance tools (data export, deletion)

#### 4.2 Advanced Analytics
- [ ] Conversation analytics dashboard
- [ ] Customer journey visualization
- [ ] Revenue attribution tracking
- [ ] Bot performance scoring

#### 4.3 Knowledge Management
- [ ] Document ingestion pipeline
- [ ] Auto-vectorization
- [ ] Knowledge graph visualization
- [ ] Version control for knowledge base

## Technology Roadmap

### Near Term (3 months)
- Migrate to gRPC for internal services
- Implement circuit breakers cho LLM calls
- Add request/response caching layer
- Optimize vector search với HNSW index

### Mid Term (6 months)
- Support for multi-language (i18n)
- Voice integration (Speech-to-Text)
- Advanced NLU với custom entity recognition
- Recommendation engine integration

### Long Term (12 months)
- Autonomous bot training với reinforcement learning
- Multi-modal support (images, videos)
- Blockchain-based conversation history
- Federated learning cho privacy-preserving training

## Success Metrics

### Technical KPIs
- **P95 Latency**: < 200ms (Tier 1), < 500ms (Tier 2), < 2s (Tier 3)
- **Uptime**: 99.9% availability
- **Cost Efficiency**: > 80% requests handled by Tier 1 + 2
- **Token Optimization**: < 2000 tokens per agentic interaction

### Business KPIs
- **Conversion Rate**: Tỷ lệ chuyển đổi từ chat sang purchase
- **Customer Satisfaction**: CSAT score > 4.5/5
- **Automation Rate**: % conversations không cần human intervention
- **Revenue Per Session**: Doanh thu trung bình mỗi conversation

---

**Last Updated**: February 2026  
**Status**: Production-ready foundation, scaling for multi-channel deployment
