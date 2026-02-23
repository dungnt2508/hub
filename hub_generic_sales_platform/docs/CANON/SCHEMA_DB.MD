# Database Schema

## Overview

The Agentic Sales Platform uses a **multi-tenant PostgreSQL database** with **pgvector** extension for semantic search. The schema is designed around the **Offering-centric** model to support multiple industries and domains.

---

## Schema Organization

Tables are organized into **6 logical groups** using naming prefixes:

| Prefix | Purpose | Scope | Examples |
|--------|---------|-------|----------|
| `system_` | Core platform capabilities | Global | `system_capability` |
| `domain_` / `knowledge_` | Domain definitions & ontology | Global | `knowledge_domain`, `domain_attribute_definition` |
| `tenant_` | Customer assets & data | Per-tenant | `tenant_offering`, `tenant_price_list` |
| `bot_` | Bot configuration & knowledge | Per-tenant | `bot`, `bot_faq`, `bot_version` |
| `runtime_` | Conversational logs | Per-session | `runtime_session`, `runtime_turn` |
| `migration_` | Data import jobs | Per-tenant | `migration_job` |

---

## Table Groups

### 1. Knowledge & Domain (Global Blueprint)

Defines **what can be sold** and **how to describe it**.

#### knowledge_domain

Industry/product categories (e.g., Electronics, Real Estate, Finance).

```sql
CREATE TABLE knowledge_domain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,  -- 'electronics', 'real_estate', 'finance'
    name TEXT NOT NULL,
    domain_type TEXT,  -- 'offering', 'business'
    description TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    flow_config JSONB,  -- Domain-specific flow configuration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Example Rows**:
```json
{
  "code": "real_estate",
  "name": "Bất Động Sản",
  "flow_config": {
    "default_state": "idle",
    "allows_comparison": true,
    "requires_analysis": true
  }
}
```

#### domain_attribute_definition

Attribute schemas per domain (e.g., "bedrooms" for Real Estate, "interest_rate" for Finance).

```sql
CREATE TABLE domain_attribute_definition (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES knowledge_domain(id),
    key TEXT NOT NULL,  -- 'bedrooms', 'area', 'interest_rate'
    value_type TEXT,  -- 'text', 'number', 'boolean', 'json'
    semantic_type TEXT,  -- 'physical', 'financial', 'categorical'
    value_constraint JSONB,  -- {'min': 0, 'max': 10} or {'enum': ['S','M','L']}
    scope TEXT,  -- 'offering' or 'variant'
    is_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(domain_id, key)
);
```

**Example Rows**:
```json
[
  {
    "domain_id": "real_estate_uuid",
    "key": "bedrooms",
    "value_type": "number",
    "value_constraint": {"min": 1, "max": 10}
  },
  {
    "domain_id": "finance_uuid",
    "key": "interest_rate",
    "value_type": "number",
    "value_constraint": {"min": 0, "max": 100}
  }
]
```

#### system_capability

Platform capabilities (e.g., search, recommendation, automation).

```sql
CREATE TABLE system_capability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES knowledge_domain(id),
    code TEXT UNIQUE NOT NULL,  -- 'offering_search', 'price_analysis'
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 2. Tenant (Customer Assets)

Customer-owned data including offerings, pricing, and inventory.

#### tenant

Root tenant entity.

```sql
CREATE TABLE tenant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',  -- 'active', 'suspended'
    plan TEXT DEFAULT 'free',  -- 'free', 'pro', 'enterprise'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### tenant_offering

The core "product/service/asset" table (replaces traditional "Product").

```sql
CREATE TABLE tenant_offering (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    domain_id UUID REFERENCES knowledge_domain(id),
    bot_id UUID,  -- Optional: offering tied to specific bot
    offering_type TEXT,  -- 'physical', 'service', 'asset', 'financial'
    code TEXT NOT NULL,  -- Tenant's internal code
    identity_key TEXT,  -- Unique identifier within tenant
    status TEXT DEFAULT 'active',  -- 'active', 'archived'
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);
```

**Examples**:

| offering_type | Example | Domain |
|---------------|---------|--------|
| `physical` | Laptop, T-shirt | Electronics, Fashion |
| `service` | English course, Spa treatment | Education, Beauty |
| `asset` | Apartment, Car | Real Estate, Auto |
| `financial` | Loan package, Insurance | Finance |

#### tenant_offering_version

Versioned data for offerings (schema, descriptions, embeddings).

```sql
CREATE TABLE tenant_offering_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offering_id UUID REFERENCES tenant_offering(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',  -- 'draft', 'active', 'archived'
    embedding VECTOR(1536),  -- For semantic search
    attributes JSONB,  -- Flexible attributes storage
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(offering_id, version)
);
```

#### tenant_offering_attribute_value

Attribute values per offering version (EAV pattern).

```sql
CREATE TABLE tenant_offering_attribute_value (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offering_version_id UUID REFERENCES tenant_offering_version(id) ON DELETE CASCADE,
    attribute_def_id UUID REFERENCES domain_attribute_definition(id),
    value_text TEXT,
    value_number NUMERIC,
    value_bool BOOLEAN,
    value_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### tenant_offering_variant

SKU-level data (color, size variations).

```sql
CREATE TABLE tenant_offering_variant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    offering_id UUID REFERENCES tenant_offering(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name TEXT,
    status TEXT DEFAULT 'active',
    attributes JSONB,  -- Variant-specific attributes
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, sku)
);
```

#### Pricing & Sales Channels

```sql
-- Sales channels (Web, Zalo, Facebook, etc.)
CREATE TABLE tenant_sales_channel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    code TEXT NOT NULL,  -- 'web', 'zalo_oa', 'facebook'
    name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- Price lists (per channel, time-based)
CREATE TABLE tenant_price_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    channel_id UUID REFERENCES tenant_sales_channel(id),
    code TEXT NOT NULL,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);


-- Variant-level pricing
CREATE TABLE tenant_variant_price (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    price_list_id UUID REFERENCES tenant_price_list(id) ON DELETE CASCADE,
    variant_id UUID REFERENCES tenant_offering_variant(id) ON DELETE CASCADE,
    currency TEXT DEFAULT 'VND',
    amount NUMERIC NOT NULL,
    compare_at NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Inventory Management

```sql
CREATE TABLE tenant_inventory_location (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    code TEXT NOT NULL,
    name TEXT,
    type TEXT,  -- 'warehouse', 'store', 'virtual'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE TABLE tenant_inventory_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    variant_id UUID REFERENCES tenant_offering_variant(id) ON DELETE CASCADE,
    location_id UUID REFERENCES tenant_inventory_location(id),
    stock_qty INTEGER DEFAULT 0,
    safety_stock INTEGER DEFAULT 0,  -- Minimum stock level
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Guardrails & Caching

```sql
-- AI safety rules
CREATE TABLE tenant_guardrail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    code TEXT NOT NULL,
    name TEXT,
    condition_expression TEXT,  -- Condition logic
    violation_action TEXT,  -- 'block', 'warn'
    fallback_message TEXT,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Semantic cache for repeated queries
CREATE TABLE tenant_semantic_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    embedding VECTOR(1536),
    hit_count INTEGER DEFAULT 0,
    last_hit_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 3. Bot (Identity & Configuration)

Bot definitions, capabilities, and knowledge base.

#### bot

Bot entity.

```sql
CREATE TABLE bot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    domain_id UUID REFERENCES knowledge_domain(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',  -- 'active', 'archived'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);
```

#### bot_version

Bot versioning for A/B testing and rollback.

```sql
CREATE TABLE bot_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID REFERENCES bot(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    flow_config JSONB,  -- Custom flow configuration
    system_prompt TEXT,  -- Bot personality & instructions
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bot_id, version)
);
```

#### bot_capability

Links bot versions to system capabilities.

```sql
CREATE TABLE bot_capability (
    bot_version_id UUID REFERENCES bot_version(id) ON DELETE CASCADE,
    capability_id UUID REFERENCES system_capability(id) ON DELETE CASCADE,
    PRIMARY KEY (bot_version_id, capability_id)
);
```

#### bot_faq

FAQ knowledge base with semantic search.

```sql
CREATE TABLE bot_faq (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    bot_id UUID REFERENCES bot(id),
    domain_id UUID REFERENCES knowledge_domain(id),
    offering_id UUID REFERENCES tenant_offering(id),  -- Optional link
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT,
    embedding VECTOR(1536),
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4. Runtime (Conversation Logs)

Real-time conversation data.

#### runtime_session

User conversation sessions.

```sql
CREATE TABLE runtime_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    bot_id UUID REFERENCES bot(id),
    bot_version_id UUID REFERENCES bot_version(id),
    channel_code TEXT,  -- 'web', 'zalo', 'facebook'
    flow_step TEXT,  -- Current lifecycle state
    flow_context JSONB,  -- Arbitrary session metadata
    ext_metadata JSONB,  -- External system data
    state_updated_at TIMESTAMP,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);
```

#### runtime_turn

Conversation history (user + bot messages).

```sql
CREATE TABLE runtime_turn (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES runtime_session(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL,  -- 'user', 'assistant', 'system'
    message TEXT NOT NULL,
    ui_metadata JSONB,  -- UI rendering data (grids, comparisons)
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### runtime_context_slot

Extracted context (entities) from conversation.

```sql
CREATE TABLE runtime_context_slot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES runtime_session(id) ON DELETE CASCADE,
    slot_key TEXT NOT NULL,  -- 'color', 'budget', 'location'
    slot_value TEXT NOT NULL,
    confidence NUMERIC,  -- Extraction confidence
    extracted_from_turn_id UUID REFERENCES runtime_turn(id),
    expires_at TIMESTAMP,  -- TTL for slot
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### runtime_decision_event

Orchestration decisions (tier selection, cost tracking).

```sql
CREATE TABLE runtime_decision_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES runtime_session(id) ON DELETE CASCADE,
    input_turn_id UUID REFERENCES runtime_turn(id),
    bot_version_id UUID REFERENCES bot_version(id),
    event_type TEXT,  -- 'tier_selection', 'tool_execution'
    decision_metadata JSONB,  -- Details about decision
    estimated_cost_usd NUMERIC,  -- LLM API cost
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### runtime_action_execution

Tool execution logs.

```sql
CREATE TABLE runtime_action_execution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES runtime_session(id) ON DELETE CASCADE,
    action_type TEXT,  -- 'tool_call', 'api_call'
    action_name TEXT,  -- Tool name
    input_params JSONB,
    output_result JSONB,
    execution_time_ms INTEGER,
    status TEXT,  -- 'success', 'error'
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 5. Migration (Data Import)

Data import/scraping jobs.

```sql
CREATE TABLE migration_job (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) NOT NULL,
    domain_id UUID REFERENCES knowledge_domain(id),
    source_type TEXT,  -- 'web_scraper', 'file_upload', 'api'
    source_url TEXT,
    status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    raw_data JSONB,  -- Scraped/uploaded data
    staged_data JSONB,  -- Parsed/validated data
    error_log TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Multi-Tenancy Strategy

### Row-Level Security

All tenant-scoped tables enforce `tenant_id` filtering:

```python
# Repository pattern
async def get_offerings(tenant_id: str):
    stmt = select(TenantOffering).where(
        TenantOffering.tenant_id == tenant_id,
        TenantOffering.is_archived == False
    )
    return await db.execute(stmt)
```

### Data Isolation

- **Application-level**: Middleware injects `tenant_id` from JWT
- **Query-level**: All queries include `WHERE tenant_id = :tenant_id`
- **Index-level**: Composite indexes start with `tenant_id`

---

## Key Design Patterns

### 1. EAV (Entity-Attribute-Value)

Flexible attributes via `tenant_offering_attribute_value`:
- Supports dynamic domains
- No schema migration for new attributes

### 2. Versioning

`tenant_offering_version` and `bot_version` support:
- A/B testing
- Rollback
- Audit trail

### 3. Vector Search (pgvector)

Semantic search on:
- `tenant_offering_version.embedding`
- `bot_faq.embedding`
- `tenant_semantic_cache.embedding`

### 4. Soft Delete

Important tables use `is_archived` instead of hard delete:
- `tenant_offering`
- `knowledge_domain`

---

## Indexes

**Critical for Performance**:

```sql
-- Multi-tenancy
CREATE INDEX idx_offering_tenant ON tenant_offering(tenant_id, is_archived);
CREATE INDEX idx_session_tenant ON runtime_session(tenant_id, started_at DESC);

-- Vector search
CREATE INDEX idx_offering_embedding ON tenant_offering_version USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_faq_embedding ON bot_faq USING ivfflat (embedding vector_cosine_ops);

-- Foreign keys
CREATE INDEX idx_offering_version_offering ON tenant_offering_version(offering_id);
CREATE INDEX idx_turn_session ON runtime_turn(session_id, created_at DESC);
```

---

**Schema Status**: Production-ready, actively used  
**Last Updated**: February 2026  
**Location**: `app/infrastructure/database/models/`
