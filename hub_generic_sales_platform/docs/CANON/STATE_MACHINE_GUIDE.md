# State Machine Guide

## Overview

The **State Machine** is a core component of the Agentic Sales Platform that controls the agent's behavior by scoping available tools based on the current conversation stage. This ensures guided user journeys, prevents invalid operations, and optimizes token usage.

## Core Concept

> **State defines the scope; Agent executes within the scope.**

The agent is powerful but constrained - it can reason freely but only has access to tools allowed in the current state.

---

## Lifecycle States

The system currently defines **10 lifecycle states** representing different stages of the customer journey:

```python
class LifecycleState(str, Enum):
    IDLE = "idle"
    BROWSING = "browsing"
    SEARCHING = "searching"
    FILTERING = "filtering"
    VIEWING = "viewing"
    COMPARING = "comparing"
    ANALYZING = "analyzing"
    PURCHASING = "purchasing"
    CLOSED = "closed"
    START = "start"  # Initial state
```

### State Descriptions

| State | Purpose | Typical User Intent |
|-------|---------|---------------------|
| **START** | Initial entry point | First message in new session |
| **IDLE** | Waiting, general chat | "Hello", casual conversation |
| **BROWSING** | General exploration | "Cho tôi xem sản phẩm" |
| **SEARCHING** | Active search | "Tìm laptop dưới 20 triệu" |
| **FILTERING** | Refining results | "Chỉ hiện màu đỏ thôi" |
| **VIEWING** | Examining details | "Xem cái thứ 2", "Chi tiết hơn" |
| **COMPARING** | Side-by-side comparison | "So sánh 2 cái" |
| **ANALYZING** | Deep analysis | "Tính vay giúp tôi" (Finance), "Định giá xe cũ" (Auto) |
| **PURCHASING** | Conversion action | "Đặt hàng", "Book lịch xem nhà" |
| **CLOSED** | Session ended | Explicit end or timeout |

---

## Tool Scoping (STATE_SKILL_MAP)

Each state defines a **whitelist of allowed tools**. This prevents the agent from calling inappropriate tools.

**Implementation**: `app/core/domain/state_machine.py`

```python
STATE_SKILL_MAP: Dict[LifecycleState, Set[str]] = {
    LifecycleState.IDLE: {
        "search_offerings",
        "compare_offerings",
        "get_market_data",
        "get_strategic_analysis",
        "trade_in_valuation",
        "credit_scoring",
        "assessment_test"
    },
    LifecycleState.BROWSING: {
        "search_offerings",
        "get_offering_details",
        "get_market_data",
        "trade_in_valuation",
        "credit_scoring",
        "assessment_test"
    },
    LifecycleState.VIEWING: {
        "get_offering_details",
        "compare_offerings",
        "get_market_data",
        "trigger_web_hook",
        "get_strategic_analysis",
        "trade_in_valuation"
    },
    LifecycleState.COMPARING: {
        "compare_offerings",
        "get_offering_details",
        "get_market_data",
        "get_strategic_analysis"
    },
    LifecycleState.ANALYZING: {
        "get_market_data",
        "get_strategic_analysis",
        "search_offerings",
        "credit_scoring",
        "trade_in_valuation"
    },
    LifecycleState.PURCHASING: {
        "trigger_web_hook",
        "search_offerings",
        "get_offering_details"
    },
    # ... (SEARCHING, FILTERING similar to BROWSING/VIEWING)
}
```

### Tool Distribution by Category

**Catalog Tools** (All domains):
- `search_offerings` - Search with filters
- `get_offering_details` - Get full details of one offering
- `compare_offerings` - Side-by-side comparison

**Financial Tools** (Finance domain):
- `get_market_data` - Market analysis, trends
- `get_strategic_analysis` - Investment recommendations
- `credit_scoring` - Credit assessment

**Automotive Tools** (Auto domain):
- `trade_in_valuation` - Trade-in price estimation

**Education Tools** (Education domain):
- `assessment_test` - Placement testing

**Integration Tools** (All domains):
- `trigger_web_hook` - External system integration (CRM, PMS, payment)

---

## State Transitions

### How States Change

States change through **tool execution results**:

```python
# Tool handler returns new state
return {
    "success": True,
    "response": "Found 5 laptops matching your criteria",
    "new_state": LifecycleState.BROWSING,
    "results": [...]
}
```

**AgentOrchestrator** reads the `new_state` and updates the session:

```python
if "new_state" in tool_result:
    new_state = tool_result["new_state"]
    await session_handler.update_flow_step(session_id, new_state, tenant_id)
```

### Valid Transitions

While not strictly enforced (flexible system), typical valid transitions:

| From | To | Trigger |
|------|----|---------| 
| IDLE | BROWSING, SEARCHING, ANALYZING | User starts exploring |
| BROWSING | VIEWING | User picks specific offering |
| VIEWING | COMPARING, PURCHASING | User wants comparison or to buy |
| COMPARING | VIEWING, PURCHASING | User picks one or proceeds |
| ANALYZING | VIEWING, PURCHASING | Analysis complete, next step |
| PURCHASING | CLOSED | Transaction complete |
| Any | IDLE | User changes topic |

---

## Processing Flow

### 1. Request Arrives

```python
# HybridOrchestrator receives message
message = "Xem cái thứ 2"
session = get_session(session_id)
current_state = session.flow_step  # e.g., "browsing"
```

### 2. State Machine Filters Tools

```python
# StateMachine.get_allowed_tools
allowed_tools = StateMachine.get_allowed_tools(current_state)
# Returns: ["get_offering_details", "search_offerings", ...]
```

### 3. Agent Reasoning (Scoped)

```python
# AgentOrchestrator sends ONLY allowed tools to LLM
llm_result = await llm_provider.generate_response(
    system_prompt="You are a sales assistant...",
    user_message=message,
    tools=allowed_tools,  # ← SCOPED, not all tools
    messages_history=history
)
```

### 4. State Update

```python
# Tool execution returns new state
tool_result = await execute_tool(tool_name, arguments)
if tool_result.get("new_state"):
    await update_session_state(session_id, tool_result["new_state"])
```

---

## Benefits of State Machine

### 1. **Predictability**
Admin knows exactly what the bot can/cannot do in each state.
- Cannot purchase before viewing
- Cannot compare without search results

### 2. **Token Optimization**
Instead of sending all 20+ tools to LLM:
- IDLE: ~7 tools
- VIEWING: ~6 tools
- COMPARING: ~4 tools

**Savings**: 50-70% reduction in tool schema tokens

### 3. **Analytics & Tracking**
Dashboard shows:
- Where users drop off (e.g., 60% abandon at VIEWING)
- Average time per state
- Conversion funnel by state

### 4. **Guardrails**
If LLM hallucinates and tries to call unauthorized tool:
```python
# Tool executor checks
if tool_name not in allowed_tools:
    return {"error": "Tool not allowed in current state"}
```

---

## Example: User Journey

### Retail Flow

```
User: "Cho tôi xem laptop"
→ State: IDLE → BROWSING
→ Tools: search_offerings
→ Result: 5 laptops shown

User: "Cái thứ 2"
→ State: BROWSING → VIEWING
→ Tools: get_offering_details
→ Result: Full specs displayed

User: "So sánh với cái 4"
→ State: VIEWING → COMPARING
→ Tools: compare_offerings
→ Result: Side-by-side table

User: "Mua cái đầu"
→ State: COMPARING → PURCHASING
→ Tools: trigger_web_hook
→ Result: Redirect to checkout
```

### Real Estate Flow

```
User: "Tìm căn 3PN ở Quận 1"
→ State: IDLE → BROWSING
→ Tools: search_offerings
→ Result: 3 properties shown

User: "Căn đầu hướng nào?"
→ State: BROWSING → VIEWING
→ Tools: get_offering_details
→ Result: Details + direction info

User: "Tính vay giúp tôi"
→ State: VIEWING → ANALYZING
→ Tools: get_market_data (mortgage calculator)
→ Result: Loan calculation displayed

User: "Đặt lịch xem nhà"
→ State: ANALYZING → PURCHASING
→ Tools: trigger_web_hook
→ Result: Calendar booking link sent
```

---

## Adding a New State

### Step 1: Define State in Domain

**File**: `app/core/domain/runtime.py`

```python
class LifecycleState(str, Enum):
    # ... existing states
    NEGOTIATING = "negotiating"  # NEW
```

### Step 2: Configure State Machine

**File**: `app/core/domain/state_machine.py`

```python
STATE_SKILL_MAP: Dict[LifecycleState, Set[str]] = {
    # ... existing states
    LifecycleState.NEGOTIATING: {
        "get_offering_details",
        "get_price_analysis",  # Hypothetical tool
        "submit_counter_offer"  # Hypothetical tool
    }
}
```

### Step 3: Update Tool Handlers

Ensure tools return `new_state: LifecycleState.NEGOTIATING` when appropriate:

```python
@agent_tools.register_tool(name="submit_counter_offer")
async def handle_counter_offer(offering_id: str, offer_price: float, **kwargs):
    # Save offer
    return {
        "success": True,
        "response": "Counter-offer submitted",
        "new_state": LifecycleState.NEGOTIATING
    }
```

### Step 4: Database Migration (if needed)

If state is stored as enum in DB:
```sql
ALTER TYPE lifecycle_state_enum ADD VALUE 'negotiating';
```

---

## Current State vs Ideal State

### ✅ Currently Implemented
- 10 lifecycle states defined
- Tool scoping per state
- Dynamic state transitions
- State persistence in database
- Background state updates

### ⚠️ Areas for Enhancement
- **Strict transition validation**: Currently allows any transition (flexible but risky)
- **State timeout**: Sessions don't auto-expire if idle too long
- **State analytics dashboard**: Exists but could be more detailed
- **Error recovery states**: Missing WAITING_USER_INPUT, ERROR states

---

## Best Practices

### Do's
✅ Always scope tools by state  
✅ Return `new_state` from tool handlers when state should change  
✅ Log state transitions for analytics  
✅ Use descriptive state names (present participle: BROWSING, VIEWING)

### Don'ts
❌ Don't bypass state machine (call tools directly)  
❌ Don't create too many states (causes tool fragmentation)  
❌ Don't hard-code state transitions (use declarative config)  
❌ Don't forget to update frontend state display

---

**Implementation Status**: Production-ready, actively used  
**Last Updated**: February 2026  
**Location**: `app/core/domain/state_machine.py`
