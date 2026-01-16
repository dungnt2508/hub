#!/bin/bash
# Production Testing Helper Script
# Usage: ./test_production.sh <api-key> <tenant-id>

set -e

API_KEY=${1:-"your-api-key"}
TENANT_ID=${2:-"your-tenant-id"}
API_URL="http://localhost:8386/api/v1/chat"
USER_ID="550e8400-e29b-41d4-a716-446655440000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Production Testing Script ===${NC}\n"

# Function to send request and display response
send_request() {
    local message=$1
    local session_id=$2
    local description=$3
    
    echo -e "${YELLOW}Test: $description${NC}"
    echo "Message: $message"
    
    local payload
    if [ -z "$session_id" ]; then
        payload=$(cat <<EOF
{
  "message": "$message",
  "user_id": "$USER_ID",
  "metadata": {
    "tenant_id": "$TENANT_ID"
  }
}
EOF
)
    else
        payload=$(cat <<EOF
{
  "message": "$message",
  "user_id": "$USER_ID",
  "session_id": "$session_id",
  "metadata": {
    "tenant_id": "$TENANT_ID"
  }
}
EOF
)
    fi
    
    response=$(curl -s -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: $API_KEY" \
      -d "$payload")
    
    echo "Response:"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
    
    # Extract session_id if present
    session_id=$(echo "$response" | jq -r '.session_id // empty' 2>/dev/null)
    echo -e "\nSession ID: $session_id\n"
    echo "---"
    echo ""
    
    echo "$session_id"
}

# Test F1.1: Session Persistence
echo -e "${GREEN}=== Test F1.1: Session Persistence ===${NC}\n"

SESSION_ID=$(send_request "Tôi muốn xin nghỉ phép" "" "F1.1.1: NEED_MORE_INFO persistence")
if [ -z "$SESSION_ID" ]; then
    echo -e "${RED}ERROR: No session_id returned${NC}"
    exit 1
fi

# Test F1.2: Slot Merge
echo -e "${GREEN}=== Test F1.2: Slot Merge ===${NC}\n"

send_request "từ ngày 2025-02-01" "$SESSION_ID" "F1.2.1: Provide start_date"
send_request "đến ngày 2025-02-05" "$SESSION_ID" "F1.2.2: Provide end_date"
send_request "nghỉ phép gia đình" "$SESSION_ID" "F1.2.3: Provide reason (should SUCCESS)"

# Test F1.3: UNKNOWN Recovery
echo -e "${GREEN}=== Test F1.3: UNKNOWN Recovery ===${NC}\n"

NEW_SESSION=$(send_request "xyz abc 123" "" "F1.3.1: UNKNOWN without last_domain")

# Test F2.1: Continuation
echo -e "${GREEN}=== Test F2.1: Continuation Check ===${NC}\n"

CONT_SESSION=$(send_request "Tôi muốn xin nghỉ phép" "" "F2.1.1: Start leave request")
send_request "mai" "$CONT_SESSION" "F2.1.2: Continue with 'mai' (should CONTINUATION)"

# Test F2.3: Next Action
echo -e "${GREEN}=== Test F2.3: Next Action ===${NC}\n"

send_request "Tôi muốn xin nghỉ phép" "" "F2.3.1: Check next_action=ASK_SLOT"

# Test F3.1: Intent Mapping
echo -e "${GREEN}=== Test F3.1: Intent Mapping From Config ===${NC}\n"

send_request "Tìm kiếm sản phẩm workflow" "" "F3.1.1: Catalog search (should map to catalog.search)"

# Test F3.3: Context Boost
echo -e "${GREEN}=== Test F3.3: Context Boost ===${NC}\n"

BOOST_SESSION=$(send_request "Tôi còn bao nhiêu ngày phép?" "" "F3.3.1: Set last_domain=hr")
send_request "Tìm kiếm thông tin" "$BOOST_SESSION" "F3.3.2: Ambiguous (should boost HR)"

# Test F4.1: Slot Validation
echo -e "${GREEN}=== Test F4.1: Slot Validation ===${NC}\n"

send_request "Tôi muốn xin nghỉ phép từ ngày 32/13/2025" "" "F4.1.1: Invalid date (should warn)"

# Test F4.2: Timeout (skip - requires waiting)
echo -e "${YELLOW}=== Test F4.2: Conversation Timeout ===${NC}\n"
echo "Skipped - requires waiting for timeout period"
echo "To test: Set CONVERSATION_TIMEOUT_MINUTES=1 and wait 1 minute"

# Test F4.3: Escalation
echo -e "${GREEN}=== Test F4.3: Escalation Path ===${NC}\n"
echo "Note: Requires ESCALATION_RETRY_THRESHOLD=2 and multiple error requests"
echo "See PRODUCTION_TESTING_GUIDE.md for detailed steps"

echo -e "\n${GREEN}=== Testing Complete ===${NC}"
echo "Check Redis for session state:"
echo "  redis-cli GET \"session:$SESSION_ID\""
