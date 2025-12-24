/**
 * JWT Key Management Service
 * 
 * RULE: Support key rotation via kid (key ID)
 * RULE: RS256 or ES256 signing
 * RULE: Expose JWKS endpoint for public key retrieval
 */

import { generateKeyPairSync, createPrivateKey, createPublicKey } from 'crypto';
import pool from '../config/database';
import { v4 as uuidv4 } from 'uuid';

export interface JWTKey {
    id: string;
    kid: string;
    algorithm: 'RS256' | 'ES256';
    public_key_pem: string;
    private_key_pem: string;
    is_active: boolean;
    is_revoked: boolean;
    rotated_at: Date | null;
    rotated_to_kid: string | null;
    created_at: Date;
    revoked_at: Date | null;
}

export class JWTKeyService {
    /**
     * Generate new RSA key pair for RS256
     */
    private generateRSAKeyPair(): { publicKey: string; privateKey: string } {
        const { publicKey, privateKey } = generateKeyPairSync('rsa', {
            modulusLength: 2048,
            publicKeyEncoding: {
                type: 'spki',
                format: 'pem',
            },
            privateKeyEncoding: {
                type: 'pkcs8',
                format: 'pem',
            },
        });

        return { publicKey, privateKey };
    }

    /**
     * Get or create active signing key
     */
    async getActiveSigningKey(): Promise<JWTKey> {
        // Try to get existing active key
        const result = await pool.query(
            `SELECT * FROM jwt_keys 
             WHERE is_active = true AND is_revoked = false 
             ORDER BY created_at DESC 
             LIMIT 1`
        );

        if (result.rows.length > 0) {
            return result.rows[0];
        }

        // No active key found, create new one
        return await this.createNewKey();
    }

    /**
     * Create new signing key
     */
    async createNewKey(algorithm: 'RS256' | 'ES256' = 'RS256'): Promise<JWTKey> {
        // Deactivate all existing keys
        await pool.query(
            `UPDATE jwt_keys SET is_active = false, rotated_at = NOW() 
             WHERE is_active = true`
        );

        // Generate key pair
        const { publicKey, privateKey } = this.generateRSAKeyPair();
        const kid = `key_${Date.now()}_${uuidv4().split('-')[0]}`;

        // Insert new key
        const insertResult = await pool.query(
            `INSERT INTO jwt_keys (
                id, kid, algorithm, public_key_pem, private_key_pem, 
                is_active, is_revoked, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, NOW()
            ) RETURNING *`,
            [
                uuidv4(),
                kid,
                algorithm,
                publicKey,
                privateKey,
                true,  // is_active
                false, // is_revoked
            ]
        );

        return insertResult.rows[0];
    }

    /**
     * Get key by kid
     */
    async getKeyByKid(kid: string): Promise<JWTKey | null> {
        const result = await pool.query(
            'SELECT * FROM jwt_keys WHERE kid = $1',
            [kid]
        );
        return result.rows[0] || null;
    }

    /**
     * Get all public keys for JWKS endpoint
     * RULE: Expose public keys for JWT verification
     */
    async getJWKSPublicKeys(): Promise<any[]> {
        // Get all non-revoked keys (active and rotated but not revoked)
        const result = await pool.query(
            `SELECT kid, algorithm, public_key_pem 
             FROM jwt_keys 
             WHERE is_revoked = false 
             ORDER BY created_at DESC`
        );

        return result.rows.map((row: { kid: string; algorithm: string; public_key_pem: string }) => {
            try {
                const publicKey = createPublicKey(row.public_key_pem);
                
                // Convert PEM to JWK format
                const jwk = publicKey.export({
                    format: 'jwk',
                }) as any;

                // Return JWK format
                const jwkEntry: any = {
                    kty: jwk.kty,  // Key type (RSA)
                    kid: row.kid,  // Key ID
                    use: 'sig',    // Use: signature
                    alg: row.algorithm,  // Algorithm (RS256)
                };

                // Add RSA-specific fields
                if (jwk.n && jwk.e) {
                    jwkEntry.n = jwk.n;  // RSA modulus
                    jwkEntry.e = jwk.e;  // RSA exponent
                }

                return jwkEntry;
            } catch (error) {
                // Skip invalid keys (log error but don't throw)
                // Using fastify logger would be better, but for now we'll return null
                return null;
            }
        }).filter((key: any): key is any => key !== null);
    }

    /**
     * Get private key for signing (only active key)
     */
    async getSigningPrivateKey(): Promise<string> {
        const key = await this.getActiveSigningKey();
        return key.private_key_pem;
    }

    /**
     * Get public key for verification by kid
     */
    async getPublicKeyByKid(kid: string): Promise<string | null> {
        const key = await this.getKeyByKid(kid);
        if (!key || key.is_revoked) {
            return null;
        }
        return key.public_key_pem;
    }

    /**
     * Rotate keys (create new active key, deactivate old ones)
     */
    async rotateKeys(): Promise<JWTKey> {
        const oldKey = await this.getActiveSigningKey();
        const newKey = await this.createNewKey();

        // Update old key to point to new key
        await pool.query(
            `UPDATE jwt_keys 
             SET rotated_to_kid = $1 
             WHERE kid = $2`,
            [newKey.kid, oldKey.kid]
        );

        return newKey;
    }

    /**
     * Revoke a key (mark as revoked, remove from active use)
     */
    async revokeKey(kid: string): Promise<void> {
        await pool.query(
            `UPDATE jwt_keys 
             SET is_revoked = true, is_active = false, revoked_at = NOW() 
             WHERE kid = $1`,
            [kid]
        );
    }
}

export default new JWTKeyService();

