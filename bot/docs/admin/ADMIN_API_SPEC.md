# Admin API Specification

API endpoints cho admin dashboard để quản lý runtime configuration.

---

## Base URL

```
/api/admin/v1
```

## Authentication

Tất cả endpoints yêu cầu JWT authentication với role `admin` hoặc `operator`.

```
Authorization: Bearer <jwt_token>
```

---

## 1. Pattern Rules

### GET /pattern-rules

List pattern rules.

**Query Params:**
- `tenant_id` (optional): Filter by tenant
- `enabled` (optional, bool): Filter by enabled status
- `limit` (default: 50): Page size
- `offset` (default: 0): Page offset

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid|null",
      "rule_name": "string",
      "enabled": true,
      "pattern_regex": "string",
      "pattern_flags": "IGNORECASE",
      "target_domain": "hr",
      "target_intent": "query_leave_balance",
      "intent_type": "OPERATION",
      "slots_extraction": {},
      "priority": 10,
      "scope": "global",
      "scope_filter": null,
      "description": "string",
      "version": 1,
      "created_by": "uuid",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

### POST /pattern-rules

Create pattern rule.

**Request:**
```json
{
  "tenant_id": "uuid|null",
  "rule_name": "HR Leave Query",
  "enabled": true,
  "pattern_regex": "còn.*ngày.*phép",
  "pattern_flags": "IGNORECASE",
  "target_domain": "hr",
  "target_intent": "query_leave_balance",
  "intent_type": "OPERATION",
  "slots_extraction": {},
  "priority": 10,
  "scope": "global",
  "description": "Match leave balance queries"
}
```

### PUT /pattern-rules/{rule_id}

Update pattern rule.

### DELETE /pattern-rules/{rule_id}

Delete pattern rule.

### PATCH /pattern-rules/{rule_id}/enable

Enable pattern rule.

### PATCH /pattern-rules/{rule_id}/disable

Disable pattern rule.

---

## 2. Keyword Hints

### GET /keyword-hints

List keyword hints.

### POST /keyword-hints

Create keyword hint.

**Request:**
```json
{
  "tenant_id": "uuid|null",
  "rule_name": "HR Keywords",
  "enabled": true,
  "domain": "hr",
  "keywords": {
    "nghỉ phép": 0.5,
    "phép năm": 0.5,
    "nhân sự": 0.4
  },
  "scope": "global",
  "description": "HR domain keywords"
}
```

---

## 3. Routing Rules

### GET /routing-rules

List routing rules.

### POST /routing-rules

Create routing rule.

**Request:**
```json
{
  "tenant_id": "uuid|null",
  "rule_name": "HR Intent Router",
  "enabled": true,
  "intent_pattern": {
    "intent": "query_leave_balance",
    "match_type": "exact"
  },
  "target_domain": "hr",
  "target_agent": null,
  "priority": 10,
  "fallback_chain": [
    {"domain": "hr", "condition": "confidence < 0.8"}
  ],
  "scope": "global"
}
```

---

## 4. Prompt Templates

### GET /prompt-templates

List prompt templates.

**Query Params:**
- `template_type`: Filter by type (system|agent|tool|rag)
- `domain`: Filter by domain
- `agent`: Filter by agent
- `active_only`: Only active versions

### POST /prompt-templates

Create prompt template.

**Request:**
```json
{
  "tenant_id": "uuid|null",
  "template_name": "HR System Prompt",
  "template_type": "system",
  "domain": "hr",
  "agent": null,
  "template_text": "You are a helpful HR assistant...",
  "variables": {
    "required": ["user_name"],
    "optional": ["context"]
  },
  "enabled": true
}
```

### GET /prompt-templates/{template_id}/versions

List all versions of a template.

### POST /prompt-templates/{template_id}/rollback

Rollback to a previous version.

**Request:**
```json
{
  "version": 2
}
```

---

## 5. Tool Permissions

### GET /tool-permissions

List tool permissions.

### POST /tool-permissions

Create tool permission.

**Request:**
```json
{
  "tenant_id": "uuid|null",
  "agent_name": "hr_agent",
  "tool_name": "create_leave_request",
  "enabled": true,
  "allowed_contexts": ["hr"],
  "rate_limit": 100,
  "required_params": {
    "start_date": "required",
    "end_date": "required"
  }
}
```

---

## 6. Guardrails

### GET /guardrails

List guardrails.

### POST /guardrails

Create guardrail.

**Request:**
```json
{
  "tenant_id": "uuid|null",
  "rule_name": "Block Sensitive Data",
  "rule_type": "hard",
  "enabled": true,
  "trigger_condition": {
    "pattern": ".*password.*",
    "confidence_threshold": 0.8
  },
  "action": "block",
  "action_params": {
    "message": "Cannot process sensitive data"
  },
  "priority": 100
}
```

---

## 7. Test Sandbox

### POST /test-sandbox

Test routing với trace.

**Request:**
```json
{
  "message": "Tôi còn bao nhiêu ngày phép?",
  "tenant_id": "uuid|null",
  "user_context": {
    "user_id": "uuid",
    "session_id": "uuid"
  }
}
```

**Response:**
```json
{
  "routing_result": {
    "domain": "hr",
    "intent": "query_leave_balance",
    "confidence": 1.0,
    "source": "PATTERN"
  },
  "trace": {
    "trace_id": "uuid",
    "spans": [
      {
        "step": "router.step.pattern",
        "input": {...},
        "output": {...},
        "duration_ms": 5
      }
    ]
  },
  "configs_used": [
    {
      "type": "pattern_rule",
      "id": "uuid",
      "rule_name": "HR Leave Query"
    }
  ]
}
```

---

## 8. Audit Logs

### GET /audit-logs

List audit logs.

**Query Params:**
- `tenant_id`: Filter by tenant
- `config_type`: Filter by config type
- `config_id`: Filter by config ID
- `changed_by`: Filter by user
- `start_date`: Start date (ISO format)
- `end_date`: End date (ISO format)
- `limit`: Page size
- `offset`: Page offset

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "tenant_id": "uuid",
      "config_type": "pattern_rule",
      "config_id": "uuid",
      "config_name": "HR Leave Query",
      "changed_by": "uuid",
      "changed_by_email": "admin@example.com",
      "action": "create",
      "old_value": null,
      "new_value": {...},
      "diff": null,
      "changed_at": "2025-01-01T00:00:00Z",
      "reason": "Initial rule creation"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

---

## Error Responses

```json
{
  "error": true,
  "message": "Error description",
  "status_code": 400,
  "details": {}
}
```

**Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `500`: Internal Server Error

