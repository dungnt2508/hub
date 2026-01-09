#!/bin/sh
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[Entrypoint] Starting bot service...${NC}"

# Only run migrations and seed data if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    # Run migrations
    echo -e "${YELLOW}[Entrypoint] Running database migrations...${NC}"
    cd /app

    # Run migrations with retry logic (in case database is not ready yet)
    max_attempts=5
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if alembic upgrade head; then
            echo -e "${GREEN}[Entrypoint] Migrations completed successfully!${NC}"
            break
        else
            attempt=$((attempt + 1))
            if [ $attempt -eq $max_attempts ]; then
                echo -e "${RED}[Entrypoint] Migration failed after $max_attempts attempts!${NC}"
                exit 1
            else
                echo -e "${YELLOW}[Entrypoint] Migration failed, retrying... (attempt $attempt/$max_attempts)${NC}"
                sleep 3
            fi
        fi
    done

    # Create default admin user
    echo -e "${YELLOW}[Entrypoint] Creating default admin user...${NC}"
    if python -m backend.alembic_migrations.auto.create_default_admin; then
        echo -e "${GREEN}[Entrypoint] Default admin user check completed!${NC}"
    else
        echo -e "${YELLOW}[Entrypoint] Warning: Failed to create default admin user (may already exist)${NC}"
    fi

    # Create routing data
    echo -e "${YELLOW}[Entrypoint] Creating routing data...${NC}"
    if python -m backend.alembic_migrations.auto.seed_routing_data; then
        echo -e "${GREEN}[Entrypoint] Create routing data completed!${NC}"
    else
        echo -e "${YELLOW}[Entrypoint] Warning: Failed to create routing data (may already exist)${NC}"
    fi

    # Create hr data
    echo -e "${YELLOW}[Entrypoint] Creating hr data...${NC}"
    if python -m backend.alembic_migrations.auto.seed_hr_data; then
        echo -e "${GREEN}[Entrypoint] Create hr data completed!${NC}"
    else
        echo -e "${YELLOW}[Entrypoint] Warning: Failed to create hr data (may already exist)${NC}"
    fi
else
    echo -e "${YELLOW}[Entrypoint] DATABASE_URL not set, skipping migrations and seed data${NC}"
fi

# Execute the main command (passed as arguments to this script)
echo -e "${GREEN}[Entrypoint] Starting application...${NC}"
exec "$@"
