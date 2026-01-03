# PHASE ROADMAP — HUB BOT SYSTEM
## PHASE 1 — GLOBAL ROUTER (DECISION CORE)

Mục tiêu duy nhất
→ Nhận message → quyết định route đúng domain → audit được.

Không trả lời người dùng.
Không xử lý nghiệp vụ.
Không “thông minh giả”.

#### Scope PHASE 1

IN

  message (string)

  user_context (đã auth)

  session_id (optional)

OUT

  RoutingResult:

  domain

  intent (optional)

  confidence

  source (pattern | embedding | llm)

  trace

Thành phần bắt buộc

- Session Management

      Redis

      last_domain

      conversation_state

      TTL

- Routing Chain

      Meta-task detection
      (help, reset, cancel, out-of-scope)

      Pattern Match (hard rule)

      Keyword Hint (soft boost)

      Embedding Classifier (API-based)

      LLM Classifier (fallback)

      UNKNOWN

- Provider Abstraction

      LiteLLM primary

      OpenAI fallback

      Timeout, retry, circuit-breaker (basic)

- Audit / Trace

    input/output mỗi step

    score

    latency

    decision source

#### Tuyệt đối KHÔNG có ở PHASE 1

❌ Domain logic

❌ HR / Ops / SAP

❌ RAG / Qdrant

❌ JWT / Auth

❌ Workflow engine

❌ Personalization

#### Kết quả hoàn thành PHASE 1

Router chạy độc lập

Có thể thêm domain không sửa router

Debug được mọi quyết định sai

## PHASE 2 — DOMAIN ENGINE (BUSINESS CORE)

Mục tiêu
→ Sau khi đã route đúng domain, xử lý nghiệp vụ đúng và sạch.

Mỗi domain = một engine độc lập.

Scope PHASE 2

IN

RoutingResult

payload (đã normalize)

session context

OUT

DomainResponse (structured)

next_action (optional)

Kiến trúc domain engine (bắt buộc)

Clean Architecture

domain_hr/
├─ entities/
├─ use_cases/
├─ ports/
├─ adapters/
└─ entrypoint/

Thành phần trong domain engine

Intent Resolver (domain-level)

Không dùng LLM bừa bãi

Ưu tiên rule + small classifier

Use Cases

Query leave

Create request

Approve

Validate policy

Ports

Repository

External API (SAP, HRM)

Notification

Adapters

SQL

SAP

REST

Email

Tuyệt đối KHÔNG có ở PHASE 2

❌ Global routing

❌ Cross-domain decision

❌ Knowledge search

Kết quả hoàn thành PHASE 2

HR bot chạy độc lập

Ops bot thêm vào không ảnh hưởng HR

Domain testable, mockable

## PHASE 3 — KNOWLEDGE ENGINE (SEMANTIC CORE)

Mục tiêu
→ Trả lời câu hỏi không phải workflow, dựa trên tài liệu.

Scope PHASE 3

IN

Query

domain (optional)

user context

OUT

Answer + sources

confidence

Thành phần

Ingestion Pipeline

Chunking

Metadata

Versioning

Vector Store

Qdrant / pgvector

Retriever

Semantic search

Hybrid (keyword + vector)

RAG Orchestrator

Context building

Token control

Hallucination guard

Integration với Domain Engine

Domain engine chủ động gọi

Router không biết knowledge tồn tại

Kết quả hoàn thành PHASE 3

Q&A policy

Tra cứu quy định

Không phá workflow engine

## PHASE 4 — EXPERIENCE & PLATFORM LAYER

Mục tiêu
→ Cá nhân hóa, vận hành, mở rộng quy mô.

Thành phần PHASE 4

Personalization

Tone

Avatar

Preferred language

Model preference

Platform

Auth

Rate limit

API Gateway

Webhook

Observability

Metrics

Tracing

Cost tracking

Admin Tools

Intent registry

Pattern editor

Audit viewer

Kết quả cuối

Multi-domain bot

Multi-tenant

Audit-ready

Scale-ready

TÓM TẮT 1 DÒNG

Phase 1: quyết định đúng

Phase 2: làm đúng việc

Phase 3: trả lời đúng kiến thức

Phase 4: dùng được lâu dài

Nếu mày phá vỡ thứ tự này → hệ thống sẽ phình, mơ hồ, không debug được.