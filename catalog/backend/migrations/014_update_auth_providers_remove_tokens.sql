-- Update auth_providers table to remove OAuth tokens
-- RULE: Do NOT store Google access tokens or refresh tokens
-- RULE: Google OAuth is used ONLY for initial identity verification

-- Remove columns that violate security rules
ALTER TABLE auth_providers 
    DROP COLUMN IF EXISTS access_token,
    DROP COLUMN IF EXISTS refresh_token;

COMMENT ON TABLE auth_providers IS 'OAuth provider bindings - stores ONLY provider_user_id mapping, NO tokens';

