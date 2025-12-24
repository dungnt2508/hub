/**
 * Internal JWT Service
 * 
 * RULE: Catalog Auth Service MUST issue INTERNAL JWTs
 * RULE: JWT MUST include: iss, aud, sub, exp, iat, jti
 * RULE: iss = "catalog-auth"
 * RULE: aud MUST be service-specific (e.g. "bot-service")
 * RULE: sub = internal user_id (NOT email, NOT google sub)
 * RULE: Access tokens are short-lived (15-30 minutes)
 */

import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { createPrivateKey, createPublicKey } from 'crypto';
import jwtKeyService from './jwt-key.service';
import { UserRole } from '@gsnake/shared-types';

export interface InternalJWTPayload {
    // Required standard claims
    iss: string;  // "catalog-auth"
    aud: string;  // Service-specific (e.g. "bot-service")
    sub: string;  // Internal user_id (UUID)
    exp: number;  // Expiration timestamp
    iat: number;  // Issued at timestamp
    jti: string;  // JWT ID (UUID)
    
    // Custom claims
    role: UserRole;
    permissions?: string[];
}

export class InternalJWTService {
    private readonly ISSUER = 'catalog-auth';
    private readonly ACCESS_TOKEN_EXPIRY_MINUTES = 30; // 30 minutes

    /**
     * Generate internal access token
     * RULE: Short-lived (15-30 minutes)
     */
    async generateAccessToken(
        userId: string,
        role: UserRole,
        audience: string,
        permissions?: string[]
    ): Promise<string> {
        // RULE: Get or create active signing key (auto-create if not exists)
        const key = await jwtKeyService.getActiveSigningKey();
        const privateKey = createPrivateKey(key.private_key_pem);

        // Prepare payload
        const now = Math.floor(Date.now() / 1000);
        const payload: InternalJWTPayload = {
            iss: this.ISSUER,
            aud: audience,
            sub: userId,  // RULE: Internal user_id, NOT email, NOT google sub
            exp: now + (this.ACCESS_TOKEN_EXPIRY_MINUTES * 60),
            iat: now,
            jti: uuidv4(),  // RULE: Unique JWT ID
            role,
            permissions: permissions || [],
        };

        // Sign with RS256 and kid header
        return jwt.sign(payload, privateKey, {
            algorithm: 'RS256',
            keyid: key.kid,  // RULE: Include kid for key rotation
        });
    }

    /**
     * Verify internal JWT token
     * RULE: Verify with public key from JWKS
     */
    async verifyToken(
        token: string,
        expectedAudience: string
    ): Promise<InternalJWTPayload> {
        try {
            // Decode header to get kid
            const decoded = jwt.decode(token, { complete: true });
            
            if (!decoded || typeof decoded === 'string') {
                throw new Error('Invalid token format');
            }

            const kid = decoded.header.kid;
            if (!kid) {
                throw new Error('Token missing kid in header');
            }

            // Get public key by kid
            const publicKeyPem = await jwtKeyService.getPublicKeyByKid(kid);
            if (!publicKeyPem) {
                throw new Error(`Key not found for kid: ${kid}`);
            }

            const publicKey = createPublicKey(publicKeyPem);

            // Verify token
            const payload = jwt.verify(token, publicKey, {
                algorithms: ['RS256'],
                issuer: this.ISSUER,
                audience: expectedAudience,
            }) as InternalJWTPayload;

            // Additional validation
            if (payload.sub !== payload.sub) {
                throw new Error('Invalid sub claim');
            }

            return payload;
        } catch (error) {
            if (error instanceof jwt.JsonWebTokenError) {
                throw new Error(`JWT verification failed: ${error.message}`);
            }
            if (error instanceof jwt.TokenExpiredError) {
                throw new Error('Token has expired');
            }
            if (error instanceof jwt.NotBeforeError) {
                throw new Error('Token not yet valid');
            }
            throw error;
        }
    }
}

export default new InternalJWTService();

