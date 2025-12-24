import pool from '../config/database';
import { RefreshTokenRecord } from '../services/refresh-token.service';

export class RefreshTokenRepository {
    async findByTokenHash(tokenHash: string): Promise<RefreshTokenRecord | null> {
        const result = await pool.query(
            'SELECT * FROM refresh_tokens WHERE token_hash = $1 LIMIT 1',
            [tokenHash]
        );
        return result.rows[0] || null;
    }

    async findByPreviousTokenHash(previousTokenHash: string): Promise<RefreshTokenRecord | null> {
        const result = await pool.query(
            'SELECT * FROM refresh_tokens WHERE previous_token_hash = $1 LIMIT 1',
            [previousTokenHash]
        );
        return result.rows[0] || null;
    }

    async findByUserId(userId: string): Promise<RefreshTokenRecord[]> {
        const result = await pool.query(
            'SELECT * FROM refresh_tokens WHERE user_id = $1 ORDER BY created_at DESC',
            [userId]
        );
        return result.rows;
    }

    async findActiveByUserId(userId: string): Promise<RefreshTokenRecord[]> {
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

export default new RefreshTokenRepository();

