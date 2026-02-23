#!/bin/bash
# Test Authentication Endpoints
# Usage: ./test-auth.sh

API_BASE_URL="${API_BASE_URL:-http://localhost:3001}"
GOOGLE_ID_TOKEN="${GOOGLE_ID_TOKEN:-}"  # Set this if you have a valid Google id_token

echo "🧪 Testing Catalog Auth Service"
echo "================================"
echo ""

# Test 1: JWKS Endpoint
echo "1. Testing JWKS Endpoint..."
echo "GET $API_BASE_URL/.well-known/jwks.json"
curl -s "$API_BASE_URL/.well-known/jwks.json" | jq '.' || echo "❌ Failed"
echo ""
echo ""

# Test 2: Google Auth (if id_token provided)
if [ -n "$GOOGLE_ID_TOKEN" ]; then
    echo "2. Testing Google Auth..."
    echo "POST $API_BASE_URL/auth/google"
    curl -s -X POST "$API_BASE_URL/auth/google" \
        -H "Content-Type: application/json" \
        -d "{
            \"id_token\": \"$GOOGLE_ID_TOKEN\",
            \"audience\": \"bot-service\"
        }" | jq '.' || echo "❌ Failed"
    echo ""
    echo ""
else
    echo "2. Skipping Google Auth test (set GOOGLE_ID_TOKEN env var)"
    echo ""
fi

# Test 3: Token Refresh (if refresh_token provided)
if [ -n "$REFRESH_TOKEN" ]; then
    echo "3. Testing Token Refresh..."
    echo "POST $API_BASE_URL/auth/refresh"
    curl -s -X POST "$API_BASE_URL/auth/refresh" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"$REFRESH_TOKEN\",
            \"audience\": \"bot-service\"
        }" | jq '.' || echo "❌ Failed"
    echo ""
    echo ""
else
    echo "3. Skipping Token Refresh test (set REFRESH_TOKEN env var)"
    echo ""
fi

# Test 4: Logout (if refresh_token provided)
if [ -n "$REFRESH_TOKEN" ]; then
    echo "4. Testing Logout..."
    echo "POST $API_BASE_URL/auth/logout"
    curl -s -X POST "$API_BASE_URL/auth/logout" \
        -H "Content-Type: application/json" \
        -d "{
            \"refresh_token\": \"$REFRESH_TOKEN\"
        }" | jq '.' || echo "❌ Failed"
    echo ""
fi

echo "✅ Tests completed"

