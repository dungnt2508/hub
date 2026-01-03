# Admin Dashboard Architecture - Runtime Config System

**Mục tiêu:** Dashboard admin cho phép cấu hình runtime bot service không cần redeploy.

---

## 1. Kiến trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────┐
│                    Admin Dashboard UI                        │
│  (React/Vue - CRUD Config, Visual Editor, Test Sandbox)    │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────┐
│              Admin API (FastAPI)                            │
│  • CRUD Routing Rules                                       │
│  • CRUD Pattern Rules                                       │
│  • CRUD Keyword Hints                                       │
│  • CRUD Prompt Templates                                    │
│  • CRUD Tool Permissions                                    │
│  • CRUD Guardrails                                          │
│  • Test Sandbox                                             │
│  • Audit Logs                                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
┌───────────▼──────────┐      ┌────────────▼──────────┐
│   PostgreSQL DB      │      │     Redis Cache       │
│  (Config Storage)    │◄─────│  (Runtime Config)     │
│                      │      │                       │
│  • routing_rules     │      │  Key: config:domain   │
│  • pattern_rules     │      │  TTL: 300s            │
│  • keyword_hints     │      │                       │
│  • prompt_templates  │      │                       │
│  • tool_permissions  │      │                       │
│  • guardrails        │      │                       │
│  • audit_logs        │      │                       │
└───────────┬──────────┘      └────────────┬──────────┘
            │                               │
            └───────────────┬───────────────┘
                            │
                ┌───────────▼───────────┐
                │  Config Loader Service│
                │  • Load from DB       │
                │  • Cache in Redis     │
                │  • Invalidate on edit │
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │   Router Runtime      │
                │  • Pattern Step       │
                │  • Keyword Step       │
                │  • Embedding Step     │
                │  • LLM Step           │
                │  • Load config dynamic│
                └───────────────────────┘
```

---

## 2. Database Schema

### 2.1. routing_rules
Routing rules: intent → domain/agent mapping với priority và fallback chain.

```sql
CREATE TABLE routing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL = global
    rule_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    
    -- Matching criteria
    intent_pattern JSONB NOT NULL,  -- { "intent": "query_leave_balance", "match_type": "exact|prefix|regex" }
    
    -- Routing decision
    target_domain VARCHAR(100),
    target_agent VARCHAR(100),  -- optional, nếu không thì dùng domain default
    target_workflow JSONB,  -- optional workflow config
    
    -- Priority & Fallback
    priority INTEGER DEFAULT 0,  -- higher = checked first
    fallback_chain JSONB,  -- [{"domain": "hr", "condition": "..."}, ...]
    
    -- Scope
    scope VARCHAR(50) DEFAULT 'global',  -- 'global' | 'per_bot' | 'per_user_group'
    scope_filter JSONB,  -- {"bot_ids": [...], "user_groups": [...]}
    
    -- Metadata
    description TEXT,
    created_by UUID,  -- admin user id
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    
    -- Indexes
    CONSTRAINT routing_rules_tenant_scope UNIQUE (tenant_id, rule_name, version)
);

CREATE INDEX idx_routing_rules_tenant_enabled ON routing_rules(tenant_id, enabled, priority DESC);
CREATE INDEX idx_routing_rules_intent_pattern ON routing_rules USING GIN(intent_pattern);
```

### 2.2. pattern_rules
Hard rules: regex patterns với priority.

```sql
CREATE TABLE pattern_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    
    -- Pattern config
    pattern_regex TEXT NOT NULL,  -- regex pattern
    pattern_flags VARCHAR(20) DEFAULT 'IGNORECASE',  -- IGNORECASE, MULTILINE, etc.
    
    -- Routing decision
    target_domain VARCHAR(100) NOT NULL,
    target_intent VARCHAR(100),
    intent_type VARCHAR(50),  -- 'OPERATION' | 'KNOWLEDGE'
    slots_extraction JSONB,  -- {"date": "regex_group_1", ...}
    
    -- Priority
    priority INTEGER DEFAULT 0,  -- higher = checked first
    
    -- Scope
    scope VARCHAR(50) DEFAULT 'global',
    scope_filter JSONB,
    
    -- Metadata
    description TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    
    CONSTRAINT pattern_rules_tenant_name UNIQUE (tenant_id, rule_name, version)
);

CREATE INDEX idx_pattern_rules_tenant_enabled ON pattern_rules(tenant_id, enabled, priority DESC);
```

### 2.3. keyword_hints
Soft rules: keyword hints với weights.

```sql
CREATE TABLE keyword_hints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    
    -- Keyword config
    domain VARCHAR(100) NOT NULL,
    keywords JSONB NOT NULL,  -- {"keyword": weight, ...}
    
    -- Scope
    scope VARCHAR(50) DEFAULT 'global',
    scope_filter JSONB,
    
    -- Metadata
    description TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT keyword_hints_tenant_domain UNIQUE (tenant_id, domain, rule_name)
);

CREATE INDEX idx_keyword_hints_tenant_enabled ON keyword_hints(tenant_id, enabled);
CREATE INDEX idx_keyword_hints_domain ON keyword_hints(domain);
```

### 2.4. prompt_templates
Prompt templates với versioning và rollback.

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL,  -- 'system' | 'agent' | 'tool' | 'rag'
    domain VARCHAR(100),  -- optional, NULL = global
    agent VARCHAR(100),  -- optional
    enabled BOOLEAN DEFAULT true,
    
    -- Template content
    template_text TEXT NOT NULL,  -- jinja2 template
    variables JSONB,  -- {"required": ["user_name"], "optional": ["context"]}
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,  -- latest active version
    
    -- Metadata
    description TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT prompt_templates_tenant_name_version UNIQUE (tenant_id, template_name, version)
);

CREATE INDEX idx_prompt_templates_tenant_active ON prompt_templates(tenant_id, template_type, is_active);
CREATE INDEX idx_prompt_templates_domain_agent ON prompt_templates(domain, agent, is_active);
```

### 2.5. tool_permissions
Tool enable/disable per agent.

```sql
CREATE TABLE tool_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    
    -- Permission config
    allowed_contexts JSONB,  -- ["hr", "operations"] - contexts where tool can be used
    rate_limit INTEGER,  -- optional rate limit per hour
    required_params JSONB,  -- validation rules
    
    -- Metadata
    description TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT tool_permissions_tenant_agent_tool UNIQUE (tenant_id, agent_name, tool_name)
);

CREATE INDEX idx_tool_permissions_tenant_agent ON tool_permissions(tenant_id, agent_name, enabled);
```

### 2.6. guardrails
Safety rules: hard rules và soft rules.

```sql
CREATE TABLE guardrails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- 'hard' | 'soft'
    enabled BOOLEAN DEFAULT true,
    
    -- Rule config
    trigger_condition JSONB NOT NULL,  -- {"pattern": "...", "intent": "...", "confidence_threshold": 0.8}
    action VARCHAR(50) NOT NULL,  -- 'block' | 'redirect' | 'flag' | 'require_confirmation'
    action_params JSONB,  -- {"redirect_to": "hr", "message": "..."}
    
    -- Scope
    scope VARCHAR(50) DEFAULT 'global',
    scope_filter JSONB,
    
    -- Priority
    priority INTEGER DEFAULT 0,
    
    -- Metadata
    description TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT guardrails_tenant_name UNIQUE (tenant_id, rule_name)
);

CREATE INDEX idx_guardrails_tenant_enabled ON guardrails(tenant_id, enabled, priority DESC);
CREATE INDEX idx_guardrails_type ON guardrails(rule_type, enabled);
```

### 2.7. config_audit_logs
Audit log cho mọi thay đổi config.

```sql
CREATE TABLE config_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- What changed
    config_type VARCHAR(50) NOT NULL,  -- 'routing_rule' | 'pattern_rule' | ...
    config_id UUID NOT NULL,
    config_name VARCHAR(255),
    
    -- Who changed
    changed_by UUID NOT NULL,  -- admin user id
    changed_by_email VARCHAR(255),
    
    -- Change details
    action VARCHAR(50) NOT NULL,  -- 'create' | 'update' | 'delete' | 'enable' | 'disable'
    old_value JSONB,  -- snapshot before change
    new_value JSONB,  -- snapshot after change
    diff JSONB,  -- {"field": {"old": "...", "new": "..."}}
    
    -- When
    changed_at TIMESTAMP DEFAULT NOW(),
    
    -- Why (optional)
    reason TEXT,
    
    CONSTRAINT config_audit_logs_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_config_audit_logs_tenant ON config_audit_logs(tenant_id, changed_at DESC);
CREATE INDEX idx_config_audit_logs_config ON config_audit_logs(config_type, config_id, changed_at DESC);
CREATE INDEX idx_config_audit_logs_user ON config_audit_logs(changed_by, changed_at DESC);
```

### 2.8. admin_users
RBAC cho admin dashboard.

```sql
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'admin' | 'operator' | 'viewer'
    
    -- Permissions (JSONB for flexibility)
    permissions JSONB DEFAULT '{}',  -- {"can_edit_routing": true, "can_view_audit": true}
    
    -- Metadata
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL = super admin
    active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_tenant_role ON admin_users(tenant_id, role, active);
```

---

## 3. Config Loader Service

### 3.1. Pseudocode

```python
class ConfigLoader:
    def __init__(self, db: Database, redis: Redis):
        self.db = db
        self.redis = redis
        self.cache_ttl = 300  # 5 minutes
    
    async def get_routing_rules(self, tenant_id: Optional[str] = None) -> List[RoutingRule]:
        cache_key = f"config:routing_rules:{tenant_id or 'global'}"
        
        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Load from DB
        rules = await self.db.query(
            "SELECT * FROM routing_rules WHERE enabled = true AND (tenant_id = $1 OR tenant_id IS NULL) ORDER BY priority DESC",
            tenant_id
        )
        
        # Cache
        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(rules))
        
        return rules
    
    async def get_pattern_rules(self, tenant_id: Optional[str] = None) -> List[PatternRule]:
        # Similar pattern...
    
    async def invalidate_cache(self, config_type: str, tenant_id: Optional[str] = None):
        pattern = f"config:{config_type}:{tenant_id or '*'}"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

### 3.2. Integration vào Router Steps

```python
class PatternMatchStep:
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self._compiled_patterns = None
        self._last_refresh = None
    
    async def _load_patterns(self, tenant_id: Optional[str] = None):
        # Refresh every 5 minutes or on cache miss
        if self._last_refresh and (time.time() - self._last_refresh) < 300:
            return
        
        rules = await self.config_loader.get_pattern_rules(tenant_id)
        
        self._compiled_patterns = [
            (re.compile(r.pattern_regex, r.pattern_flags), r)
            for r in sorted(rules, key=lambda x: x.priority, reverse=True)
        ]
        
        self._last_refresh = time.time()
    
    async def execute(self, message: str, tenant_id: Optional[str] = None):
        await self._load_patterns(tenant_id)
        
        for pattern, rule in self._compiled_patterns:
            if pattern.search(message):
                return {
                    "matched": True,
                    "domain": rule.target_domain,
                    "intent": rule.target_intent,
                    "intent_type": rule.intent_type,
                    "slots": self._extract_slots(message, pattern, rule.slots_extraction),
                    "confidence": 1.0,
                    "source": "PATTERN",
                }
        
        return {"matched": False}
```

---

## 4. API Design (FastAPI)

### 4.1. Routing Rules API

```python
# GET /api/admin/routing-rules
# Query params: tenant_id?, enabled?, limit, offset
async def list_routing_rules(
    tenant_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: AdminUser = Depends(get_current_admin_user)
) -> List[RoutingRuleResponse]

# POST /api/admin/routing-rules
async def create_routing_rule(
    rule: RoutingRuleCreate,
    current_user: AdminUser = Depends(get_current_admin_user),
    audit_service: AuditService = Depends(get_audit_service)
) -> RoutingRuleResponse:
    # Create rule
    # Audit log
    # Invalidate cache

# PUT /api/admin/routing-rules/{rule_id}
async def update_routing_rule(
    rule_id: UUID,
    rule: RoutingRuleUpdate,
    current_user: AdminUser = Depends(get_current_admin_user),
    audit_service: AuditService = Depends(get_audit_service)
) -> RoutingRuleResponse

# DELETE /api/admin/routing-rules/{rule_id}
async def delete_routing_rule(...)

# PATCH /api/admin/routing-rules/{rule_id}/enable
async def enable_routing_rule(...)

# PATCH /api/admin/routing-rules/{rule_id}/disable
async def disable_routing_rule(...)
```

### 4.2. Pattern Rules API

Tương tự routing_rules.

### 4.3. Keyword Hints API

Tương tự.

### 4.4. Prompt Templates API

```python
# POST /api/admin/prompt-templates
async def create_prompt_template(...)

# GET /api/admin/prompt-templates/{template_id}/versions
async def list_template_versions(...)

# POST /api/admin/prompt-templates/{template_id}/rollback
async def rollback_template_version(...)
```

### 4.5. Test Sandbox API

```python
# POST /api/admin/test-sandbox
async def test_routing(
    request: TestSandboxRequest,  # {message: str, tenant_id?: str, user_context?: dict}
    current_user: AdminUser = Depends(get_current_admin_user)
) -> TestSandboxResponse:  # {routing_result: RouterResponse, trace: RouterTrace, configs_used: [...]}
    # Run router với test message
    # Return full trace + configs used
```

### 4.6. Audit Logs API

```python
# GET /api/admin/audit-logs
async def list_audit_logs(
    tenant_id?: str,
    config_type?: str,
    config_id?: UUID,
    changed_by?: UUID,
    start_date?: datetime,
    end_date?: datetime,
    limit: int = 100,
    offset: int = 0
) -> List[AuditLogResponse]
```

---

## 5. Frontend Dashboard Structure

### 5.1. Screens

```
/admin
├── /dashboard              # Overview (stats, recent changes)
├── /routing
│   ├── /rules              # CRUD routing rules
│   └── /visual-editor      # Visual flow editor (drag-drop rules)
├── /patterns               # CRUD pattern rules
├── /keywords               # CRUD keyword hints
├── /prompts                # CRUD prompt templates
│   └── /:id/versions       # Version history & rollback
├── /tools                  # Tool permissions management
├── /guardrails             # Safety rules management
├── /test-sandbox           # Test routing với trace view
├── /audit-logs             # Audit log viewer
└── /settings               # User settings, RBAC
```

### 5.2. Components

```
components/
├── ConfigEditor/
│   ├── RoutingRuleEditor.tsx
│   ├── PatternRuleEditor.tsx
│   ├── KeywordHintEditor.tsx
│   └── PromptTemplateEditor.tsx
├── VisualEditor/
│   ├── RuleFlowCanvas.tsx      # Drag-drop visual editor
│   └── RuleNode.tsx
├── TestSandbox/
│   ├── MessageInput.tsx
│   ├── TraceViewer.tsx         # Decision trace visualization
│   └── ConfigUsedViewer.tsx
├── AuditLog/
│   ├── AuditLogTable.tsx
│   └── DiffViewer.tsx          # Before/after diff
└── Common/
    ├── EnableDisableToggle.tsx
    ├── PrioritySlider.tsx
    └── ScopeFilter.tsx
```

---

## 6. Scaling Strategy (Future: NVIDIA Stack)

### 6.1. Config Distribution
- Use Redis Pub/Sub để broadcast config changes đến tất cả bot instances
- Config versioning để support gradual rollout

### 6.2. NVIDIA Integration
- Replace embedding classifier với NVIDIA NIM embeddings
- Replace LLM classifier với NVIDIA NIM models
- Config loader vẫn giữ nguyên interface

### 6.3. Multi-Region
- Config sync qua distributed cache (Redis Cluster)
- Read replicas cho audit logs

---

## 7. Security & RBAC

### 7.1. Roles

- **admin**: Full access (CRUD tất cả config, manage users)
- **operator**: CRUD config (không thể manage users, không thể xóa audit logs)
- **viewer**: Read-only (xem config, test sandbox, audit logs)

### 7.2. Permissions Matrix

| Action | admin | operator | viewer |
|--------|-------|----------|--------|
| View configs | ✅ | ✅ | ✅ |
| Create/Edit configs | ✅ | ✅ | ❌ |
| Delete configs | ✅ | ❌ | ❌ |
| Enable/Disable configs | ✅ | ✅ | ❌ |
| Test sandbox | ✅ | ✅ | ✅ |
| View audit logs | ✅ | ✅ | ✅ |
| Manage users | ✅ | ❌ | ❌ |

---

## 8. Implementation Priority

1. **Phase 1**: Database schema + Config Loader + Pattern Rules CRUD
2. **Phase 2**: Refactor PatternMatchStep để dùng config từ DB
3. **Phase 3**: Keyword Hints + Prompt Templates CRUD
4. **Phase 4**: Routing Rules + Visual Editor
5. **Phase 5**: Test Sandbox + Audit Logs
6. **Phase 6**: RBAC + Frontend Dashboard
7. **Phase 7**: Tool Permissions + Guardrails

---

**Status**: Architecture Design Complete  
**Next**: Implementation Phase 1

