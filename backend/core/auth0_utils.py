"""
Auth0 Token Verification Utilities
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError as JWTError
from jwt.algorithms import RSAAlgorithm
from typing import Optional
import httpx
from functools import lru_cache

from core.auth0_config import get_auth0_settings


security = HTTPBearer()


@lru_cache()
def get_auth0_public_key():
    """Fetch Auth0 public key for token verification"""
    settings = get_auth0_settings()
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    
    try:
        response = httpx.get(jwks_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Auth0 JWKS: {e}")
        return None


def verify_auth0_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify Auth0 JWT token and return decoded payload
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        dict: Decoded token payload containing user info
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    settings = get_auth0_settings()
    token = credentials.credentials
    
    try:
        # Get public key
        jwks = get_auth0_public_key()
        if not jwks:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify token - JWKS unavailable"
            )
        
        # Decode and verify token
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
        
        # Convert JWK to public key object for PyJWT
        public_key = RSAAlgorithm.from_jwk(rsa_key)
        
        # Verify and decode
        payload = jwt.decode(
            token,
            public_key,
            algorithms=settings.AUTH0_ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/"
        )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


def verify_auth0_jwt(token: str) -> dict:
    """
    Raw verification for string tokens (used by core.authentication)
    """
    settings = get_auth0_settings()
    try:
        jwks = get_auth0_public_key()
        if not jwks:
            raise Exception("JWKS unavailable")
        
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise Exception("Key not found")
        
        # Convert JWK to public key object for PyJWT
        public_key = RSAAlgorithm.from_jwk(rsa_key)
        
        payload = jwt.decode(
            token,
            public_key,
            algorithms=settings.AUTH0_ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/"
        )
        return payload
    except Exception as e:
        # print(f"Auth0 Raw Verify Failed: {e}")
        raise e
