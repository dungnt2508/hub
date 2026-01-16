# TESTING QUICK REFERENCE

## Quick Start

### 1. Setup
```bash
# Start services
redis-server
# Start bot API
cd bot && python -m uvicorn backend.interface.multi_tenant_bot_api:app --port 8386
```

### 2. Run Tests

**Python Script:**
```bash
python scripts/test_production.py --api-key <key> --tenant-id <id>
```

**Bash Script:**
```bash
./scripts/test_production.sh <api-key> <tenant-id>
```

**PowerShell Script:**
```powershell
.\scripts\test_production.ps1 -ApiKey <key> -TenantId <id>
```

---

## Manual Test Commands

### Test Session Persistence (F1.1)
```bash
# Request 1: NEED_MORE_INFO
curl -X POST http://localhost:8386/api/v1/chat \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tôi muốn xin nghỉ phép", "user_id": "550e8400-e29b-41d4-a716-446655440000", "metadata": {"tenant_id": "<id>"}}'

# Save session_id từ response, sau đó:
# Request 2: SUCCESS
curl -X POST http://localhost:8386/api/v1/chat \
  -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tôi còn bao nhiêu ngày phép?", "user_id": "550e8400-e29b-41d4-a716-446655440000", "session_id": "<session-id>", "metadata": {"tenant_id": "<id>"}}'
```

### Test Slot Merge (F1.2)
```bash
# Turn 1: Start request
curl ... -d '{"message": "Tôi muốn xin nghỉ phép", ...}'

# Turn 2: Provide start_date
curl ... -d '{"message": "từ ngày 2025-02-01", "session_id": "<id>", ...}'

# Turn 3: Provide end_date
curl ... -d '{"message": "đến ngày 2025-02-05", "session_id": "<id>", ...}'

# Turn 4: Provide reason
curl ... -d '{"message": "nghỉ phép gia đình", "session_id": "<id>", ...}'
```

### Test Continuation (F2.1)
```bash
# Start request
curl ... -d '{"message": "Tôi muốn xin nghỉ phép", ...}'

# Continue with slot value
curl ... -d '{"message": "mai", "session_id": "<id>", ...}'
# Expected: source="CONTINUATION"
```

### Test UNKNOWN Recovery (F1.3)
```bash
# Without last_domain
curl ... -d '{"message": "xyz abc 123", ...}'
# Expected: options=["HR", "Catalog", "DBA"]

# With last_domain (after HR request)
curl ... -d '{"message": "xyz abc 123", "session_id": "<hr-session-id>", ...}'
# Expected: options=["hr", "Khác"]
```

---

## Verify Session State

```bash
# Get session
redis-cli GET "session:<session-id>"

# Check specific fields
redis-cli GET "session:<session-id>" | jq '.pending_intent'
redis-cli GET "session:<session-id>" | jq '.slots_memory'
redis-cli GET "session:<session-id>" | jq '.conversation_state'
```

---

## Check Logs

```bash
# Router logs
tail -f logs/bot.log | grep "router"

# Session logs
tail -f logs/bot.log | grep "session"

# Domain logs
tail -f logs/bot.log | grep "domain"
```

---

## Common Test Scenarios

### Scenario 1: Complete Leave Request Flow
1. "Tôi muốn xin nghỉ phép" → NEED_MORE_INFO
2. "từ ngày mai" → NEED_MORE_INFO (start_date set)
3. "đến ngày 2025-02-05" → NEED_MORE_INFO (end_date set)
4. "nghỉ phép gia đình" → SUCCESS

### Scenario 2: Cross-Domain
1. "Tôi còn bao nhiêu ngày phép?" → SUCCESS (HR)
2. "Tìm kiếm sản phẩm" → SUCCESS (Catalog)
3. "Thông tin về nghỉ phép" → Route về HR (boost)

### Scenario 3: Timeout
1. Start request → NEED_MORE_INFO
2. Wait 10 minutes (or set CONVERSATION_TIMEOUT_MINUTES=1)
3. Send new message → Should clear pending state

---

## Expected Results Checklist

- [ ] Session persists after NEED_MORE_INFO
- [ ] Session persists after SUCCESS
- [ ] Slots accumulate across turns
- [ ] Continuation works with slot values
- [ ] UNKNOWN has recovery options
- [ ] Next action is returned
- [ ] State machine transitions correctly
- [ ] Context boost works
- [ ] Slot validation catches invalid formats
- [ ] Timeout clears pending state
- [ ] Escalation triggers after retry threshold

---

## Troubleshooting

**Session not persisting?**
- Check Redis connection: `redis-cli ping`
- Check logs for "Session saved" or errors

**Continuation not working?**
- Check session has `pending_intent` and `active_domain`
- Check router trace for "router.step.continuation"

**State machine errors?**
- Check `conversation_state` in session
- Verify state transitions in logs

---

**Xem chi tiết:** `docs/PRODUCTION_TESTING_GUIDE.md`
