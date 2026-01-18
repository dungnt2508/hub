#!/bin/bash
set -e

echo "Starting Bot V2 Backend..."

# Wait for database to be ready (if needed)
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database to be ready..."
    # Extract host and port from DATABASE_URL
    # Format: postgresql+asyncpg://user:pass@host:port/db
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
        until nc -z $DB_HOST $DB_PORT 2>/dev/null; do
            echo "Waiting for database at $DB_HOST:$DB_PORT..."
            sleep 1
        done
        echo "Database is ready!"
    fi
fi

# Run migrations if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    echo "Running database migrations..."
    alembic upgrade head || {
        echo "Migration failed, but continuing..."
    }
fi

# Execute the main command
exec "$@"
