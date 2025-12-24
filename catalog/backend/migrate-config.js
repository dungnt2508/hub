const dotenv = require('dotenv');
const path = require('path');

// Try to load .env file (optional - env vars can come from docker-compose)
const envPath = path.join(__dirname, '.env');
const result = dotenv.config({ path: envPath });

if (result.error && result.error.code !== 'ENOENT') {
    // Only log if it's not a "file not found" error
    console.warn('Warning loading .env file:', result.error.message);
}

const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
    console.error('DATABASE_URL is not defined. Please set it via environment variables.');
    process.exit(1);
} else {
    // Mask password for logging
    const maskedUrl = dbUrl.replace(/:([^:@]+)@/, ':****@');
    console.log('Using DATABASE_URL:', maskedUrl);
}

// node-pg-migrate v7 with timestamp: false expects files in format: 001_name.sql
// But it may still try to parse timestamp. Let's use a custom migration runner instead
// or ensure files are in the correct format

module.exports = {
    'database-url': process.env.DATABASE_URL,
    'migrations-dir': 'migrations',
    'migrations-table': 'pgmigrations',
    dir: 'migrations',
    direction: 'up',
    schema: 'public',
    count: Infinity,
    'file-extension': '.sql',
    verbose: true,
    // For files like 001_name.sql, node-pg-migrate may need explicit timestamp handling
    // Try without timestamp: false first, or use a different migration tool
};
