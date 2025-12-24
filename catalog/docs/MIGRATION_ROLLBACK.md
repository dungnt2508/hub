# Migration Rollback Guide

This document describes how to rollback database migrations if needed.

## Migration Files

All migration files are located in `backend/migrations/`:
- `001_create_users_table.sql` → `down/001_down_create_users_table.sql`
- `002_create_personas_table.sql` → `down/002_down_create_personas_table.sql`
- `003_create_articles_table.sql` → `down/003_down_create_articles_table.sql`
- `004_create_fetch_schedules_table.sql` → `down/004_down_create_fetch_schedules_table.sql`
- `005_create_tool_requests_table.sql` → `down/005_down_create_tool_requests_table.sql`
- `006_update_schema_for_multisource.sql` → `down/006_down_update_schema_for_multisource.sql`
- `007_create_products_table.sql` → `down/007_down_create_products_table.sql`
- `008_add_role_and_approval_system.sql` → `down/008_down_add_role_and_approval_system.sql`

## Manual Rollback Procedure

**⚠️ WARNING: Rollback will delete data. Always backup database before rollback!**

### Step 1: Backup Database

```bash
# Create backup
pg_dump -h localhost -U gsnake1102_user -d gsnake1102 > backup_before_rollback.sql
```

### Step 2: Execute Down Migrations in Reverse Order

Rollback migrations must be executed in reverse order (newest to oldest):

```bash
cd backend

# Connect to database
psql -h localhost -U gsnake1102_user -d gsnake1102

# Execute down migrations in order:
\i migrations/down/008_down_add_role_and_approval_system.sql
\i migrations/down/007_down_create_products_table.sql
\i migrations/down/006_down_update_schema_for_multisource.sql
\i migrations/down/005_down_create_tool_requests_table.sql
\i migrations/down/004_down_create_fetch_schedules_table.sql
\i migrations/down/003_down_create_articles_table.sql
\i migrations/down/002_down_create_personas_table.sql
\i migrations/down/001_down_create_users_table.sql
```

### Step 3: Verify Rollback

```sql
-- Check tables are dropped
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Should only see system tables (pgmigrations if using node-pg-migrate)
```

## Rollback Script (Alternative)

You can also use the provided script:

```bash
cd backend
node scripts/rollback-migrations.js
```

**Note:** You need to create `scripts/rollback-migrations.js` if using node-pg-migrate with down migrations.

## Using node-pg-migrate

If using `node-pg-migrate` CLI, you can rollback one migration at a time:

```bash
# Rollback last migration
npm run migrate:down

# Rollback multiple migrations (e.g., 3 migrations)
npm run migrate:down -- -c 3
```

## Important Notes

1. **Data Loss**: Down migrations will delete tables and data. Always backup first!
2. **Order Matters**: Execute down migrations in reverse order (newest first)
3. **Foreign Keys**: Down migrations handle CASCADE drops, but be careful with dependencies
4. **Production**: Test rollback on staging first before using in production

## Emergency Restore

If something goes wrong, restore from backup:

```bash
# Drop and recreate database
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS gsnake1102;"
psql -h localhost -U postgres -c "CREATE DATABASE gsnake1102 OWNER gsnake1102_user;"

# Restore from backup
psql -h localhost -U gsnake1102_user -d gsnake1102 < backup_before_rollback.sql
```

