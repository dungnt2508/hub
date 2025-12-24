-- Create jwt_keys table for key rotation
-- RULE: Support key rotation via kid (key ID)
-- RULE: RS256/ES256 keys stored securely

CREATE TABLE IF NOT EXISTS jwt_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kid VARCHAR(50) NOT NULL UNIQUE,  -- Key ID (used in JWT header)
    
    -- Key type and algorithm
    algorithm VARCHAR(10) NOT NULL CHECK (algorithm IN ('RS256', 'ES256')),
    
    -- Public key (PEM format) - can be exposed via JWKS
    public_key_pem TEXT NOT NULL,
    
    -- Private key (PEM format) - encrypted at application level if needed
    private_key_pem TEXT NOT NULL,
    
    -- Key status
    is_active BOOLEAN NOT NULL DEFAULT true,  -- Active key for signing
    is_revoked BOOLEAN NOT NULL DEFAULT false,  -- Revoked key (still in JWKS for validation)
    
    -- Rotation metadata
    rotated_at TIMESTAMP NULL,  -- When this key was rotated out
    rotated_to_kid VARCHAR(50) NULL,  -- New key ID that replaced this one
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jwt_keys_kid ON jwt_keys(kid);
CREATE INDEX IF NOT EXISTS idx_jwt_keys_active ON jwt_keys(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_jwt_keys_revoked ON jwt_keys(is_revoked) WHERE is_revoked = false;

COMMENT ON TABLE jwt_keys IS 'JWT signing keys for RS256/ES256 - supports key rotation via kid';
COMMENT ON COLUMN jwt_keys.kid IS 'Key ID - used in JWT header (kid claim)';
COMMENT ON COLUMN jwt_keys.public_key_pem IS 'Public key in PEM format - exposed via JWKS endpoint';
COMMENT ON COLUMN jwt_keys.private_key_pem IS 'Private key in PEM format - used for signing JWTs';
COMMENT ON COLUMN jwt_keys.is_active IS 'Active key for signing new tokens';
COMMENT ON COLUMN jwt_keys.is_revoked IS 'Revoked keys still in JWKS for validation of existing tokens';

