/**
 * Google OAuth Verification Service
 * 
 * RULE: Google OAuth is used ONLY for initial identity verification
 * RULE: Verify Google id_token with Google public keys
 * RULE: Do NOT propagate Google tokens downstream
 * RULE: Do NOT store Google access tokens
 */

import { OAuth2Client } from 'google-auth-library';
import { authConfig } from '../config/auth';

export interface GoogleIdTokenPayload {
    sub: string;  // Google user ID
    email: string;
    email_verified: boolean;
    name?: string;
    picture?: string;
    iss: string;  // Issuer (should be 'accounts.google.com' or 'https://accounts.google.com')
    aud: string;  // Audience (should be our client ID)
    exp: number;  // Expiration
    iat: number;  // Issued at
}

export class GoogleAuthService {
    private client: OAuth2Client;

    constructor() {
        this.client = new OAuth2Client(
            authConfig.google.clientId,
            authConfig.google.clientSecret
        );
    }

    /**
     * Verify Google id_token
     * RULE: Verify id_token with Google public keys
     */
    async verifyIdToken(idToken: string): Promise<GoogleIdTokenPayload> {
        try {
            // Verify token with Google
            const ticket = await this.client.verifyIdToken({
                idToken,
                audience: authConfig.google.clientId,
            });

            const payload = ticket.getPayload();

            if (!payload) {
                throw new Error('Invalid Google id_token: no payload');
            }

            // Validate required fields
            if (!payload.sub) {
                throw new Error('Invalid Google id_token: missing sub');
            }

            if (!payload.email) {
                throw new Error('Invalid Google id_token: missing email');
            }

            if (!payload.email_verified) {
                throw new Error('Google email not verified');
            }

            return {
                sub: payload.sub,
                email: payload.email,
                email_verified: payload.email_verified === true,
                name: payload.name,
                picture: payload.picture,
                iss: payload.iss || '',
                aud: payload.aud || '',
                exp: payload.exp || 0,
                iat: payload.iat || 0,
            };
        } catch (error) {
            if (error instanceof Error) {
                throw new Error(`Google id_token verification failed: ${error.message}`);
            }
            throw new Error('Google id_token verification failed: unknown error');
        }
    }
}

export default new GoogleAuthService();

