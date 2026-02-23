/**
 * Test Authentication Endpoints
 * Usage: node scripts/test-auth.js
 */

const axios = require('axios');

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3001';

async function testJWKS() {
    console.log('1. Testing JWKS Endpoint...');
    try {
        const response = await axios.get(`${API_BASE_URL}/.well-known/jwks.json`);
        console.log('✅ JWKS Endpoint:', JSON.stringify(response.data, null, 2));
        return response.data;
    } catch (error) {
        console.error('❌ JWKS Endpoint failed:', error.message);
        return null;
    }
}

async function testGoogleAuth(idToken, audience = 'bot-service') {
    console.log('\n2. Testing Google Auth...');
    if (!idToken) {
        console.log('⚠️  Skipping (set GOOGLE_ID_TOKEN env var)');
        return null;
    }
    
    try {
        const response = await axios.post(`${API_BASE_URL}/auth/google`, {
            id_token: idToken,
            audience,
        });
        console.log('✅ Google Auth successful');
        console.log('Response:', JSON.stringify(response.data, null, 2));
        return response.data;
    } catch (error) {
        console.error('❌ Google Auth failed:', error.response?.data || error.message);
        return null;
    }
}

async function testRefreshToken(refreshToken, audience = 'bot-service') {
    console.log('\n3. Testing Token Refresh...');
    if (!refreshToken) {
        console.log('⚠️  Skipping (set REFRESH_TOKEN env var)');
        return null;
    }
    
    try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
            audience,
        });
        console.log('✅ Token Refresh successful');
        console.log('Response:', JSON.stringify(response.data, null, 2));
        return response.data;
    } catch (error) {
        console.error('❌ Token Refresh failed:', error.response?.data || error.message);
        return null;
    }
}

async function testLogout(refreshToken) {
    console.log('\n4. Testing Logout...');
    if (!refreshToken) {
        console.log('⚠️  Skipping (set REFRESH_TOKEN env var)');
        return null;
    }
    
    try {
        const response = await axios.post(`${API_BASE_URL}/auth/logout`, {
            refresh_token: refreshToken,
        });
        console.log('✅ Logout successful');
        console.log('Response:', JSON.stringify(response.data, null, 2));
        return response.data;
    } catch (error) {
        console.error('❌ Logout failed:', error.response?.data || error.message);
        return null;
    }
}

async function main() {
    console.log('🧪 Testing Catalog Auth Service');
    console.log('='.repeat(50));
    console.log(`API Base URL: ${API_BASE_URL}\n`);
    
    // Test JWKS
    await testJWKS();
    
    // Test Google Auth
    const googleIdToken = process.env.GOOGLE_ID_TOKEN;
    const authResult = await testGoogleAuth(googleIdToken);
    
    // Test Refresh Token
    const refreshToken = process.env.REFRESH_TOKEN || authResult?.data?.refresh_token;
    const refreshResult = await testRefreshToken(refreshToken);
    
    // Test Logout
    const logoutRefreshToken = refreshToken || authResult?.data?.refresh_token;
    await testLogout(logoutRefreshToken);
    
    console.log('\n✅ Tests completed');
}

main().catch(console.error);

