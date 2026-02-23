import pool from '../config/database';
import { v4 as uuidv4 } from 'uuid';

export type AuthProviderRecord = {
    id: string;
    user_id: string;
    provider: string;
    provider_user_id: string;
    // RULE: Do NOT store access_token or refresh_token
    created_at: Date;
    updated_at: Date;
};

export class AuthProviderRepository {
    async findByProviderUser(provider: string, providerUserId: string): Promise<AuthProviderRecord | null> {
        const result = await pool.query(
            'SELECT * FROM auth_providers WHERE provider = $1 AND provider_user_id = $2 LIMIT 1',
            [provider, providerUserId]
        );
        return result.rows[0] || null;
    }

    async findByUserAndProvider(userId: string, provider: string): Promise<AuthProviderRecord | null> {
        const result = await pool.query(
            'SELECT * FROM auth_providers WHERE user_id = $1 AND provider = $2 LIMIT 1',
            [userId, provider]
        );
        return result.rows[0] || null;
    }

    async upsert(data: {
        user_id: string;
        provider: string;
        provider_user_id: string;
        // RULE: Do NOT accept access_token or refresh_token
    }): Promise<AuthProviderRecord> {
        const now = new Date();
        const id = uuidv4();

        // RULE: Only store provider_user_id mapping, NO tokens
        const result = await pool.query(
            `INSERT INTO auth_providers (
                id, user_id, provider, provider_user_id, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6
            )
            ON CONFLICT (provider, provider_user_id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                updated_at = EXCLUDED.updated_at
            RETURNING *`,
            [
                id,
                data.user_id,
                data.provider,
                data.provider_user_id,
                now,
                now,
            ]
        );

        return result.rows[0];
    }
}

export default new AuthProviderRepository();

