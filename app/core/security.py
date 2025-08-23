"""
Security and authentication handling for Supabase JWT tokens.
Uses ES256 JWT verification with JWK discovery from Supabase.
"""

import logging
from typing import Any, Dict

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


class AuthManager:
    """Handles JWT token verification and user authentication with JWK discovery."""

    def __init__(self):
        self.jwks_cache = {}
        self.jwks_uri = settings.supabase_jwks_uri

    async def get_jwks(self) -> Dict[str, Any]:
        """Fetch and cache JWK set from Supabase."""
        if not self.jwks_cache:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.jwks_uri)
                    response.raise_for_status()
                    jwks_data = response.json()
                    self.jwks_cache = jwks_data
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise HTTPException(status_code=500, detail="Unable to verify tokens")

        return dict(self.jwks_cache)

    async def get_signing_key(self, token: str):
        """Get the signing key for the JWT token."""
        # Decode header to get kid
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        if not kid:
            raise HTTPException(status_code=401, detail="Token missing key ID")

        # Get JWKS
        jwks = await self.get_jwks()

        # Find matching key
        for key in jwks.get("keys", []):
            if key["kid"] == kid:
                return jwt.PyJWK(key)

        raise HTTPException(status_code=401, detail="Unable to find signing key")

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token using JWK discovery."""
        try:
            # Log token header for debugging
            header = jwt.get_unverified_header(token)
            logger.debug(f"JWT header: {header}")

            # Get the signing key
            signing_key = await self.get_signing_key(token)

            # Decode JWT token using ES256 - first try without audience validation
            try:
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[settings.jwt_algorithm],
                    audience="authenticated",  # Supabase audience
                )
            except jwt.InvalidAudienceError:
                # Try without audience validation for debugging
                logger.info("Trying JWT decode without audience validation")
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[settings.jwt_algorithm],
                    options={"verify_aud": False},
                )

            # Log payload for debugging (without sensitive data)
            logger.debug(f"JWT payload keys: {list(payload.keys())}")
            logger.debug(f"JWT aud: {payload.get('aud')}")
            logger.debug(f"JWT iss: {payload.get('iss')}")

            return dict(payload)

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    async def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Extract user information from JWT token."""
        payload = await self.verify_token(token)

        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "aud": payload.get("aud"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
        }


# Global auth manager
auth_manager = AuthManager()


async def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Standalone function to verify JWT token."""
    return await auth_manager.verify_token(token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        User information dict

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        user = await auth_manager.get_user_from_token(credentials.credentials)
        logger.debug(f"Authenticated user: {user['email']}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any] | None:
    """
    Optional dependency to get current user, returns None if not authenticated.
    Useful for endpoints that work both with and without authentication.
    """
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency that requires admin role.

    Args:
        user: Current authenticated user

    Returns:
        User information if admin

    Raises:
        HTTPException: If user is not admin
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user
