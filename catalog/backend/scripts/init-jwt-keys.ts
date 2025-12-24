/**
 * Initialize JWT Keys
 * 
 * RULE: Create initial signing key for JWT tokens
 * Run this script after migrations to create first key
 * 
 * Usage: 
 *   npm run init-jwt-keys
 *   hoặc: tsx scripts/init-jwt-keys.ts
 */

import jwtKeyService from '../src/services/jwt-key.service';
import '../src/config/database'; // Initialize database connection

async function initKeys() {
    console.log('🔑 Initializing JWT Keys...');
    console.log('='.repeat(50));
    
    try {
        // Check if active key exists
        const existingKey = await jwtKeyService.getActiveSigningKey();
        
        if (existingKey) {
            console.log('✅ Active key already exists:');
            console.log(`   - kid: ${existingKey.kid}`);
            console.log(`   - algorithm: ${existingKey.algorithm}`);
            console.log(`   - created_at: ${existingKey.created_at}`);
            console.log('\n⚠️  No action needed - key already exists');
            return;
        }
        
        // Create new key
        console.log('Creating new signing key...');
        const newKey = await jwtKeyService.createNewKey('RS256');
        
        console.log('✅ Key created successfully:');
        console.log(`   - kid: ${newKey.kid}`);
        console.log(`   - algorithm: ${newKey.algorithm}`);
        console.log(`   - is_active: ${newKey.is_active}`);
        console.log(`   - created_at: ${newKey.created_at}`);
        console.log('\n✅ JWT keys initialized!');
        console.log('\nYou can now verify JWKS endpoint:');
        console.log('   curl http://localhost:3001/.well-known/jwks.json');
        
    } catch (error: any) {
        console.error('❌ Failed to initialize keys:', error.message);
        if (error.stack) {
            console.error(error.stack);
        }
        process.exit(1);
    }
}

initKeys();

