"""
Security and authentication handling for Supabase JWT tokens.
Uses modern RS256 JWT verification with Supabase public keys.
"""

import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


class AuthManager:
    """Handles JWT token verification and user authentication."""
    
    def __init__(self):
        self.public_key = self._prepare_public_key()
    
    def _prepare_public_key(self) -> str:
        """Prepare the public key for JWT verification."""
        public_key = settings.supabase_jwt_public_key
        
        # Add PEM headers if not present
        if not public_key.startswith("-----BEGIN"):
            public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
        
        return public_key
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            # Decode JWT token using RS256
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[settings.jwt_algorithm],
                audience="authenticated"  # Supabase audience
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    def get_user_from_token(self, token: str) -> Dict[str, Any]:
        """Extract user information from JWT token."""
        payload = self.verify_token(token)
        
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "aud": payload.get("aud"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }


# Global auth manager
auth_manager = AuthManager()


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Standalone function to verify JWT token."""
    return auth_manager.verify_token(token)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
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
        user = auth_manager.get_user_from_token(credentials.credentials)
        logger.debug(f"Authenticated user: {user['email']}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any] | None:
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