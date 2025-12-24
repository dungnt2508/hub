const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

// Load env from docker-compose environment variables
const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
  console.error('DATABASE_URL is not defined');
  process.exit(1);
}

const pool = new Pool({
  connectionString: dbUrl,
});

async function runAllMigrations() {
  const client = await pool.connect();
  
  try {
    // Create migrations table if it doesn't exist
    await client.query(`
      CREATE TABLE IF NOT EXISTS pgmigrations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        run_on TIMESTAMP NOT NULL DEFAULT NOW()
      );
    `);

    // Get migrations directory
    const migrationsDir = path.join(__dirname, '../migrations');
    
    // Read all migration files, sort by number prefix
    const files = fs.readdirSync(migrationsDir)
      .filter(file => file.endsWith('.sql') && !file.includes('down'))
      .sort((a, b) => {
        const numA = parseInt(a.match(/^(\d+)/)?.[1] || '0');
        const numB = parseInt(b.match(/^(\d+)/)?.[1] || '0');
        return numA - numB;
      });

    console.log(`Found ${files.length} migration files`);

    for (const file of files) {
      // Check if migration already ran
      const checkResult = await client.query(
        'SELECT name FROM pgmigrations WHERE name = $1',
        [file]
      );

      if (checkResult.rows.length > 0) {
        console.log(`⏭️  Skipping ${file} (already applied)`);
        continue;
      }

      const migrationPath = path.join(migrationsDir, file);
      const sql = fs.readFileSync(migrationPath, 'utf8');

      console.log(`🔄 Running migration: ${file}`);
      
      try {
        await client.query('BEGIN');
        await client.query(sql);
        
        // Record migration
        await client.query(
          'INSERT INTO pgmigrations (name) VALUES ($1)',
          [file]
        );
        
        await client.query('COMMIT');
        console.log(`✅ Migration ${file} completed successfully!`);
      } catch (error) {
        await client.query('ROLLBACK');
        
        // Check if it's an "already exists" error (table/column already exists)
        if (error.message.includes('already exists') || 
            error.message.includes('duplicate') ||
            error.message.includes('relation') && error.message.includes('already exists')) {
          console.log(`⚠️  Migration ${file} may have already been applied, recording it...`);
          await client.query('BEGIN');
          await client.query(
            'INSERT INTO pgmigrations (name) VALUES ($1) ON CONFLICT (name) DO NOTHING',
            [file]
          );
          await client.query('COMMIT');
        } else {
          throw error;
        }
      }
    }

    console.log('✅ All migrations completed!');
  } catch (error) {
    console.error('❌ Migration failed:', error.message);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

runAllMigrations().catch((error) => {
  console.error(error);
  process.exit(1);
});

