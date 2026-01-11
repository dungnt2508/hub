#!/bin/bash

# Phase 2 Test Runner
# Run all HR domain tests to verify implementation

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      🧪 PHASE 2 - HR DOMAIN TESTS RUNNER 🧪               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counters
TOTAL=0
PASSED=0
FAILED=0

run_test() {
    local test_name="$1"
    local test_file="$2"
    
    echo -e "${BLUE}Running: $test_name${NC}"
    
    if pytest "$test_file" -v --tb=short; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}\n"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}\n"
        ((FAILED++))
    fi
    
    ((TOTAL++))
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Install with: pip install pytest${NC}"
    exit 1
fi

# Change to project directory
cd "$(dirname "$0")" || exit

echo -e "${BLUE}Running Unit Tests...${NC}\n"

# Run unit tests
run_test "HR Use Cases Unit Tests" \
    "bot/backend/tests/unit/test_hr_use_cases.py"

run_test "HR Repository Unit Tests" \
    "bot/backend/tests/unit/test_hr_repository.py"

echo -e "${BLUE}Running Integration Tests...${NC}\n"

# Run integration tests
run_test "HR Domain Integration Tests" \
    "bot/backend/tests/integration/test_hr_domain.py"

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  TEST SUMMARY                             ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "│ Total:  $TOTAL"
echo "│ Passed: ${GREEN}$PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "│ Failed: ${RED}$FAILED${NC}"
else
    echo "│ Failed: 0"
fi
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi

