#!/bin/sh
set -e

echo "🚀 Starting Catalog Backend..."

# Wait for database to be ready using Node.js
echo "⏳ Waiting for database to be ready..."
node -e "
const { Pool } = require('pg');
const pool = new Pool({
  host: process.env.DB_HOST || 'hub_postgres',
  port: parseInt(process.env.DB_PORT || '5432'),
  user: process.env.DB_USER || 'catalog_user',
  password: process.env.DB_PASSWORD || 'catalog_password',
  database: process.env.DB_NAME || 'catalog_db',
  connectionTimeoutMillis: 5000,
});

async function waitForDb() {
  let retries = 30;
  while (retries > 0) {
    try {
      await pool.query('SELECT 1');
      console.log('✅ Database is ready!');
      await pool.end();
      process.exit(0);
    } catch (err) {
      retries--;
      if (retries === 0) {
        console.error('❌ Database connection failed after 30 retries');
        process.exit(1);
      }
      console.log('   Database is unavailable - sleeping...');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

waitForDb();
" || exit 1

# Run migrations
echo "🔄 Running database migrations..."
cd /app/backend && npm run migrate || {
  echo "⚠️  Migration failed or already applied, continuing..."
  # Don't exit on migration failure - might be already applied
}
cd /app

# Start the application
echo "🎯 Starting application..."
exec "$@"

