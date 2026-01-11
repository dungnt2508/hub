"""
DBA Seed Routing Data - Quick Start

Files Created:
  1. backend/alembic_migrations/auto/seed_dba_routing_data.py (Main seed script)
  2. backend/scripts/seed_dba_routing_data.py (Wrapper script)

Features:
  ✅ 11 Pattern Rules - Map DBA keywords to use case intents
  ✅ 2 Keyword Hint Sets - Performance + Analysis keywords
  ✅ 11 Routing Rules - Route intents to DBA domain
  ✅ 4 System Prompts - DBA-specific prompts
  ✅ Anti-Duplicate Logic - Prevents data duplication on redeploy
  ✅ Easy Cleanup - --clean flag to remove all DBA data

Usage:
  # Seed data
  python backend/scripts/seed_dba_routing_data.py
  
  # Or from alembic_migrations/auto
  python -m backend.alembic_migrations.auto.seed_dba_routing_data
  
  # Clean all DBA data
  python backend/scripts/seed_dba_routing_data.py --clean

Features:
  
1. Anti-Duplicate Logic:
   - Checks if rule_name already exists before creating
   - Uses rule_exists() function to prevent duplicates
   - Tracks created vs skipped counts
   - Safe for repeated runs and redeployments

2. DBA Use Cases Covered:
   - analyze_slow_query
   - check_index_health
   - detect_blocking
   - analyze_wait_stats
   - analyze_query_regression
   - detect_deadlock_pattern
   - analyze_io_pressure
   - capacity_forecast
   - validate_custom_sql
   - compare_sp_blitz_vs_custom
   - incident_triage

3. Pattern Rules:
   - 11 patterns mapped to 11 use cases
   - Vietnamese keywords and patterns
   - Proper priorities (70-95)
   - Clear descriptions

4. Keyword Hints:
   - Performance keywords (query, performance, optimization)
   - Analysis keywords (analysis, incident, forecast)
   - Priority scores for relevance

5. Routing Rules:
   - 11 rules, one per DBA intent
   - Exact matching on intent
   - Target domain: "dba"
   - Priority-based routing

6. System Prompts:
   - Performance Analysis prompt
   - Query Optimization prompt
   - Incident Resolution prompt
   - Capacity Planning prompt

How Anti-Duplicate Works:

The rule_exists() function:
  1. Fetches all existing rules
  2. Compares rule_name field
  3. Returns True if found
  4. Returns False if not found
  
Before creating each rule:
  - Calls rule_exists() check
  - If exists: logs and skips (increments skipped count)
  - If not exists: creates new rule (increments created count)

Safe Redeployment:
  - First deploy: Creates all 26 items
  - Redeploy same version: Skips all 26 items
  - Update with new rules: Creates only new ones

Output Example:
  ✅ Đã tạo dữ liệu routing cho DBA domain thành công!
  
  📝 Dữ liệu đã tạo:
     - Pattern rules: 11 rules (DBA use cases)
     - Keyword hints: 2 keywords (database, performance)
     - Routing rules: 11 rules (map to DBA intents)
     - Prompt templates: 4 templates (DBA prompts)

Integration with Deployment:

Option 1: Manual Before Deployment
  python backend/scripts/seed_dba_routing_data.py

Option 2: Automated in Dockerfile
  RUN python -m backend.alembic_migrations.auto.seed_dba_routing_data

Option 3: In Deployment Script
  #!/bin/bash
  cd /app/bot
  python backend/scripts/seed_dba_routing_data.py

Cleanup When Needed:
  # Remove all DBA routing data
  python backend/scripts/seed_dba_routing_data.py --clean
  
  # This removes:
  - All DBA pattern rules (11)
  - All DBA keyword hints (2)
  - All DBA routing rules (11)
  - All DBA prompt templates (4)
"""

# Implementation Notes:

"""
1. Rule Name Format:
   "DBA - {Description}" (for pattern/routing rules)
   "DBA Domain - {Description}" (for keyword hints)
   "DBA - {Description}" (for prompt templates)

2. Domain Field Always "dba":
   - target_domain: "dba"
   - domain: "dba"
   - Ensures easy filtering and cleanup

3. Intent Mapping:
   - Pattern Rule: rule_name → target_intent
   - Routing Rule: intent_pattern.intent → target_intent
   - Direct 1:1 mapping for clarity

4. Priority Assignment:
   - Pattern Rules: 70-95 (higher = more specific)
   - Routing Rules: 70-95 (higher = higher priority)
   - Keyword Hints: 0.65-0.95 (confidence scores)

5. Error Handling:
   - Graceful fallback if rule_exists fails
   - Warning logged, continues with next item
   - Detailed error messages for debugging
   - Safe disconnect in finally block

6. Idempotency:
   - Script safe to run multiple times
   - No data corruption
   - Consistent behavior
   - Clear logging of what's skipped

Usage Recommendations:

1. First Run:
   python backend/scripts/seed_dba_routing_data.py
   ✅ Creates all 26 items (11+2+11+4)

2. Subsequent Runs:
   python backend/scripts/seed_dba_routing_data.py
   ⏭️  Skips all 26 items (idempotent)

3. Verify Creation:
   Check in admin dashboard:
   - Pattern Rules: Should see 11 DBA rules
   - Keyword Hints: Should see 2 DBA hints
   - Routing Rules: Should see 11 DBA rules
   - Prompt Templates: Should see 4 DBA prompts

4. During Redeploy:
   Just run script again
   ✅ Safe, no duplicates
   ⏭️  Skips existing items
   ✅ New items added if any

5. For Cleanup:
   python backend/scripts/seed_dba_routing_data.py --clean
   🗑️  Removes all DBA data
   ✅ Safe, only removes DBA items

Database Changes:
  - pattern_rules: +11 rows
  - keyword_hints: +2 rows
  - routing_rules: +11 rows
  - prompt_templates: +4 rows
  - Total: +28 rows

Rollback:
  Use --clean flag to remove all DBA routing data safely
  No other data affected
"""
