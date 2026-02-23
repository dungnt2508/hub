-- Create refresh_tokens table
-- RULE: Refresh tokens MUST be hashed and stored in database
-- RULE: Database is source of truth for refresh tokens

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Token hash (SHA-256 or bcrypt of the opaque token)
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    
    -- Token rotation support
    previous_token_hash VARCHAR(255) NULL,  -- Previous token hash (for rotation)
    
    -- Revocation
    revoked_at TIMESTAMP NULL,
    revoked_reason VARCHAR(100) NULL,  -- e.g., 'logout', 'reuse_detected', 'manual'
    
    -- Expiration
    expires_at TIMESTAMP NOT NULL,
    
    -- Metadata
    device_info JSONB,  -- Optional: device/browser info for audit
    ip_address INET,    -- Optional: IP address for audit
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked_at ON refresh_tokens(revoked_at) WHERE revoked_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Index for finding active tokens for a user
-- Note: Cannot use NOW() in index predicate (not immutable), so we only filter by revoked_at
-- Application code should check expires_at > NOW() in queries
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_active 
    ON refresh_tokens(user_id, expires_at, revoked_at) 
    WHERE revoked_at IS NULL;

COMMENT ON TABLE refresh_tokens IS 'Internal refresh tokens - opaque strings, hashed before storage';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA-256 hash of the refresh token (never store plain token)';
COMMENT ON COLUMN refresh_tokens.previous_token_hash IS 'Hash of previous token (for rotation - old token becomes previous)';
COMMENT ON COLUMN refresh_tokens.revoked_at IS 'Timestamp when token was revoked (NULL = active)';
COMMENT ON COLUMN refresh_tokens.revoked_reason IS 'Reason for revocation: logout, reuse_detected, manual';

