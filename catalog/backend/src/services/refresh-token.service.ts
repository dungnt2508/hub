/**
 * Refresh Token Service
 * 
 * RULE: Refresh tokens are opaque random strings
 * RULE: Refresh tokens MUST be hashed before storage
 * RULE: Implement refresh token rotation
 * RULE: Reuse of old refresh token MUST revoke entire session
 */

import crypto from 'crypto';
import pool from '../config/database';
import { v4 as uuidv4 } from 'uuid';

export interface RefreshTokenRecord {
    id: string;
    user_id: string;
    token_hash: string;
    previous_token_hash: string | null;
    revoked_at: Date | null;
    revoked_reason: string | null;
    expires_at: Date;
    device_info: any | null;
    ip_address: string | null;
    created_at: Date;
    updated_at: Date;
    last_used_at: Date | null;
}

export class RefreshTokenService {
    private readonly TOKEN_LENGTH = 64; // 64 bytes = 128 hex characters
    private readonly TOKEN_EXPIRY_DAYS = 7; // 7 days

    /**
     * Generate random opaque refresh token
     */
    private generateToken(): string {
        return crypto.randomBytes(this.TOKEN_LENGTH).toString('hex');
    }

    /**
     * Hash token using SHA-256
     * RULE: Hash before storage
     */
    private hashToken(token: string): string {
        return crypto.createHash('sha256').update(token).digest('hex');
    }

    /**
     * Create new refresh token for user
     */
    async createToken(
        userId: string,
        options?: {
            deviceInfo?: any;
            ipAddress?: string;
        }
    ): Promise<{ token: string; expiresAt: Date }> {
        // Generate opaque token
        const token = this.generateToken();
        const tokenHash = this.hashToken(token);

        // Calculate expiry
        const expiresAt = new Date();
        expiresAt.setDate(expiresAt.getDate() + this.TOKEN_EXPIRY_DAYS);

        // Insert into database
        await pool.query(
            `INSERT INTO refresh_tokens (
                id, user_id, token_hash, expires_at, 
                device_info, ip_address, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, NOW(), NOW()
            )`,
            [
                uuidv4(),
                userId,
                tokenHash,
                expiresAt,
                options?.deviceInfo ? JSON.stringify(options.deviceInfo) : null,
                options?.ipAddress || null,
            ]
        );

        return { token, expiresAt };
    }

    /**
     * Validate and rotate refresh token
     * RULE: Rotate refresh token on each use
     * RULE: Reuse of old token revokes entire session
     */
    async validateAndRotateToken(token: string): Promise<{
        userId: string;
        newToken: string;
        newExpiresAt: Date;
    }> {
        const tokenHash = this.hashToken(token);

        // Find token by hash
        const result = await pool.query(
            `SELECT * FROM refresh_tokens 
             WHERE token_hash = $1 
             LIMIT 1`,
            [tokenHash]
        );

        if (result.rows.length === 0) {
            // Check if this is a reused old token (check if token_hash matches a previous_token_hash)
            const reuseCheck = await pool.query(
                `SELECT user_id FROM refresh_tokens 
                 WHERE previous_token_hash = $1 
                 LIMIT 1`,
                [tokenHash]
            );

            if (reuseCheck.rows.length > 0) {
                // RULE: Reuse detected - revoke entire session
                const userId = reuseCheck.rows[0].user_id;
                await this.revokeAllUserTokens(userId, 'reuse_detected');
                throw new Error('Refresh token reuse detected - all sessions revoked');
            }

            throw new Error('Invalid refresh token');
        }

        const record = result.rows[0] as RefreshTokenRecord;

        // Check if revoked
        if (record.revoked_at) {
            throw new Error('Refresh token has been revoked');
        }

        // Check if expired
        if (new Date(record.expires_at) < new Date()) {
            throw new Error('Refresh token has expired');
        }

        // RULE: Rotate token - generate new token
        const newToken = this.generateToken();
        const newTokenHash = this.hashToken(newToken);
        const newExpiresAt = new Date();
        newExpiresAt.setDate(newExpiresAt.getDate() + this.TOKEN_EXPIRY_DAYS);

        // Update old token: mark as revoked with reason 'rotated' and set previous_token_hash = current hash
        await pool.query(
            `UPDATE refresh_tokens 
             SET revoked_at = NOW(), 
                 revoked_reason = 'rotated',
                 updated_at = NOW(),
                 previous_token_hash = $1
             WHERE id = $2`,
            [tokenHash, record.id]
        );

        // Create new token with previous_token_hash pointing to old token
        await pool.query(
            `INSERT INTO refresh_tokens (
                id, user_id, token_hash, previous_token_hash, expires_at,
                device_info, ip_address, created_at, updated_at, last_used_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, NOW(), NOW(), NOW()
            )`,
            [
                uuidv4(),
                record.user_id,
                newTokenHash,
                tokenHash, // previous_token_hash = old token hash (for reuse detection)
                newExpiresAt,
                record.device_info,
                record.ip_address,
            ]
        );

        return {
            userId: record.user_id,
            newToken,
            newExpiresAt,
        };
    }

    /**
     * Revoke refresh token
     * RULE: Logout revokes refresh token
     */
    async revokeToken(token: string, reason: string = 'logout'): Promise<void> {
        const tokenHash = this.hashToken(token);

        await pool.query(
            `UPDATE refresh_tokens 
             SET revoked_at = NOW(), revoked_reason = $1, updated_at = NOW() 
             WHERE token_hash = $2 AND revoked_at IS NULL`,
            [reason, tokenHash]
        );
    }

    /**
     * Revoke all tokens for a user
     * RULE: Used when token reuse is detected
     */
    async revokeAllUserTokens(userId: string, reason: string): Promise<void> {
        await pool.query(
            `UPDATE refresh_tokens 
             SET revoked_at = NOW(), revoked_reason = $1, updated_at = NOW() 
             WHERE user_id = $2 AND revoked_at IS NULL`,
            [reason, userId]
        );
    }

    /**
     * Get active tokens for user (for audit/admin)
     */
    async getUserActiveTokens(userId: string): Promise<RefreshTokenRecord[]> {
        const result = await pool.query(
            `SELECT * FROM refresh_tokens 
             WHERE user_id = $1 
               AND revoked_at IS NULL 
               AND expires_at > NOW() 
             ORDER BY created_at DESC`,
            [userId]
        );

        return result.rows;
    }
}

export default new RefreshTokenService();

