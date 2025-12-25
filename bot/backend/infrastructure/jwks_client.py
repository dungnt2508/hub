"""
Microsoft JWKS Client - Fetch and cache Microsoft Teams JWT public keys
Task 1.1: Implement Microsoft JWKS client
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json

from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError


class MicrosoftJWKSClient:
    """
    Microsoft JWKS client with caching.
    
    Fetches public keys from Microsoft's JWKS endpoint and caches them.
    Handles JWK rotation automatically.
    
    Reference:
    - https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-authentication-components
    - https://login.microsoftonline.com/common/.well-known/openid-configuration
    """
    
    # Microsoft Teams JWKS endpoint
    # For Bot Framework, use: https://login.botframework.com/v1/.well-known/openid_configuration
    # Then get jwks_uri from the response
    TEAMS_JWKS_URL = "https://login.botframework.com/v1/.well-known/jwks"
    
    # Cache TTL: 24 hours (JWKs don't rotate frequently)
    CACHE_TTL_SECONDS = 86400
    
    def __init__(self, jwks_url: Optional[str] = None):
        """
        Initialize JWKS client.
        
        Args:
            jwks_url: Custom JWKS URL (defaults to Microsoft Teams endpoint)
        """
        self.jwks_url = jwks_url or self.TEAMS_JWKS_URL
        self._cache: Dict[str, Any] = {}
        self._cache_expiry: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def fetch_jwks(self) -> Dict[str, Any]:
        """
        Fetch JWKS from Microsoft endpoint.
        
        Returns:
            JWKS document with keys array
            
        Raises:
            ExternalServiceError: If fetch fails
        """
        client = await self._get_client()
        
        try:
            logger.debug(f"Fetching JWKS from {self.jwks_url}")
            response = await client.get(self.jwks_url)
            response.raise_for_status()
            
            jwks = response.json()
            
            # Validate JWKS structure
            if "keys" not in jwks or not isinstance(jwks["keys"], list):
                raise ExternalServiceError("Invalid JWKS format: missing keys array")
            
            logger.info(f"Fetched {len(jwks['keys'])} keys from JWKS")
            return jwks
        
        except httpx.HTTPStatusError as e:
            logger.error(f"JWKS fetch HTTP error: {e.response.status_code}")
            raise ExternalServiceError(f"Failed to fetch JWKS: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"JWKS fetch request error: {e}")
            raise ExternalServiceError(f"Failed to fetch JWKS: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching JWKS: {e}", exc_info=True)
            raise ExternalServiceError(f"Failed to fetch JWKS: {e}") from e
    
    async def get_jwks(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get JWKS (from cache or fetch).
        
        Args:
            force_refresh: Force refresh cache
            
        Returns:
            JWKS document
        """
        # Check cache
        if not force_refresh and self._cache and self._cache_expiry:
            if datetime.now() < self._cache_expiry:
                logger.debug("Using cached JWKS")
                return self._cache
        
        # Fetch fresh JWKS
        jwks = await self.fetch_jwks()
        
        # Update cache
        self._cache = jwks
        self._cache_expiry = datetime.now() + timedelta(seconds=self.CACHE_TTL_SECONDS)
        
        logger.info("JWKS cache updated")
        return jwks
    
    def get_key_by_kid(self, jwks: Dict[str, Any], kid: str) -> Optional[Dict[str, Any]]:
        """
        Get JWK by key ID (kid).
        
        Args:
            jwks: JWKS document
            kid: Key ID from JWT header
            
        Returns:
            JWK dict or None if not found
        """
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None
    
    def jwk_to_pem(self, jwk: Dict[str, Any]) -> str:
        """
        Convert JWK to PEM format for JWT verification.
        
        Args:
            jwk: JWK dict with n, e, kty
            
        Returns:
            PEM-formatted public key string
            
        Raises:
            ValueError: If JWK format invalid
        """
        try:
            kty = jwk.get("kty")
            if kty != "RSA":
                raise ValueError(f"Unsupported key type: {kty}")
            
            # Extract modulus (n) and exponent (e)
            n = jwk.get("n")
            e = jwk.get("e")
            
            if not n or not e:
                raise ValueError("Missing n or e in JWK")
            
            # Decode base64url-encoded values
            import base64
            
            # Base64URL decode
            def base64url_decode(value: str) -> bytes:
                # Add padding if needed
                padding = 4 - len(value) % 4
                if padding != 4:
                    value += "=" * padding
                # Replace URL-safe characters
                value = value.replace("-", "+").replace("_", "/")
                return base64.b64decode(value)
            
            n_bytes = base64url_decode(n)
            e_bytes = base64url_decode(e)
            
            # Convert to integers
            n_int = int.from_bytes(n_bytes, byteorder="big")
            e_int = int.from_bytes(e_bytes, byteorder="big")
            
            # Create RSA public key
            public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
            
            # Serialize to PEM
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return pem.decode("utf-8")
        
        except Exception as e:
            logger.error(f"Failed to convert JWK to PEM: {e}", exc_info=True)
            raise ValueError(f"Invalid JWK format: {e}") from e
    
    async def get_public_key(self, kid: str) -> str:
        """
        Get public key in PEM format for given kid.
        
        Args:
            kid: Key ID from JWT header
            
        Returns:
            PEM-formatted public key
            
        Raises:
            ExternalServiceError: If key not found
        """
        # Get JWKS
        jwks = await self.get_jwks()
        
        # Find key by kid
        jwk = self.get_key_by_kid(jwks, kid)
        if not jwk:
            # Try refreshing cache in case of key rotation
            logger.warning(f"Key {kid} not found in cache, refreshing JWKS")
            jwks = await self.get_jwks(force_refresh=True)
            jwk = self.get_key_by_kid(jwks, kid)
            
            if not jwk:
                raise ExternalServiceError(f"Key {kid} not found in JWKS")
        
        # Convert to PEM
        return self.jwk_to_pem(jwk)


# Global JWKS client instance
_jwks_client: Optional[MicrosoftJWKSClient] = None


def get_jwks_client() -> MicrosoftJWKSClient:
    """Get global JWKS client instance"""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = MicrosoftJWKSClient()
    return _jwks_client


async def close_jwks_client():
    """Close global JWKS client"""
    global _jwks_client
    if _jwks_client:
        await _jwks_client.close()
        _jwks_client = None

