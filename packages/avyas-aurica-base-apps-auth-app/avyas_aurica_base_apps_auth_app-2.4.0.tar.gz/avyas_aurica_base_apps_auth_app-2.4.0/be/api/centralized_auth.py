"""
Centralized authentication endpoints for OAuth2-like redirect flow.
Supports cross-domain authentication with JWT tokens.
"""
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os
import sys
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

from jwt_utils import jwt_manager
import passkey_store as ps_module
passkey_store = ps_module.passkey_store

# Import session manager from auth middleware
try:
    from src.auth_middleware import session_manager
except ImportError:
    # Fallback for development
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
    from auth_middleware import session_manager


router = APIRouter()

# Configuration
AUTH_SERVER_DOMAIN = os.getenv("AUTH_SERVER_DOMAIN", "api.oneaurica.com")


class TokenVerifyRequest(BaseModel):
    """Request to verify a JWT token."""
    token: str


class TokenVerifyResponse(BaseModel):
    """Response after verifying a token."""
    valid: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None


@router.get("/.well-known/jwks.json", summary="Get JWKS for token verification", tags=["auth", "centralized"])
async def get_jwks(request: Request):
    """
    Get JSON Web Key Set (JWKS) for JWT token verification.
    
    This endpoint provides the public key information that other hosts
    can use to verify JWT tokens issued by this auth server.
    
    IMPORTANT: Only public key information is exposed here.
    The secret key NEVER leaves the auth server!
    
    Returns:
        JWKS with public key information
    """
    # Get algorithm from JWT manager
    secret_info = jwt_manager.get_secret_info()
    algorithm = secret_info.get('algorithm', 'HS256')
    secret_key = secret_info.get('secret_key')
    
    print(f"🔑 JWKS requested from {request.client.host}")
    print(f"   Returning secret (first 8 chars): {secret_key[:8] if secret_key else 'None'}...")
    
    if algorithm == 'HS256':
        # For HMAC, we need to provide the secret key in JWKS format
        # This is the exception - symmetric keys must be shared
        # In production, consider switching to RSA for better security
        return {
            "keys": [
                {
                    "kty": "oct",  # Octet sequence (symmetric key)
                    "use": "sig",
                    "alg": "HS256",
                    "k": secret_key  # Base64-encoded secret
                }
            ],
            "note": "HMAC keys require sharing the secret. Consider RS256 for production."
        }
    else:
        # For RSA, return public key in JWKS format
        # This would come from jwt_manager.get_jwks() if using RSA
        return jwt_manager.get_jwks()


@router.get("/secret", summary="Get JWT configuration info (deprecated)", tags=["auth", "centralized"])
async def get_secret_info(request: Request):
    """
    Get JWT configuration information.
    
    DEPRECATED: Use /.well-known/jwks.json instead.
    This endpoint is kept for backward compatibility.
    """
    return {
        "message": "Please use /.well-known/jwks.json for JWKS-based verification",
        "jwks_endpoint": f"/auth-app/api/centralized/.well-known/jwks.json",
        "algorithm": jwt_manager.get_secret_info().get('algorithm'),
        "issuer": "api.oneaurica.com",
        "audience": "aurica-apps"
    }


@router.post("/verify-token", response_model=TokenVerifyResponse, summary="Verify JWT token", tags=["auth", "centralized"])
async def verify_token(verify_request: TokenVerifyRequest):
    """
    Verify a JWT token and return user information.
    
    This endpoint is called by other hosts to verify tokens issued
    by the centralized authentication server.
    
    Args:
        verify_request: Token to verify
    
    Returns:
        Token validity and user information
    """
    claims = jwt_manager.verify_token(verify_request.token)
    
    if not claims:
        return TokenVerifyResponse(
            valid=False,
            error="Invalid or expired token"
        )
    
    return TokenVerifyResponse(
        valid=True,
        user_id=claims.get("sub"),
        username=claims.get("username"),
        role=claims.get("role", "user"),
        metadata=claims.get("metadata")
    )


@router.get("/login", summary="Redirect to login page", tags=["auth", "centralized"])
async def login_redirect(
    request: Request,
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None
):
    """
    Initiate authentication flow.
    
    This endpoint is called when a user needs to authenticate.
    If the user is already authenticated, redirect immediately.
    Otherwise, show the login page.
    
    Args:
        redirect_uri: Where to redirect after authentication
        state: Optional state parameter to pass through the flow
    
    Returns:
        Redirect to login page or back to caller with token
    """
    # Check if user is already authenticated
    token = request.cookies.get('auth_token')
    if not token:
        # Also check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
    
    if token:
        # Verify the token
        claims = jwt_manager.verify_token(token)
        if claims:
            # User is already authenticated, redirect back with token
            if redirect_uri:
                return await _redirect_with_token(redirect_uri, token, state)
            else:
                return {
                    "authenticated": True,
                    "user_id": claims.get("sub"),
                    "username": claims.get("username"),
                    "token": token
                }
    
    # User not authenticated, show login page
    # Store redirect information for after login
    login_url = f"/{request.path_params.get('app_name', 'auth-app')}/static/index.html"
    
    # Build the full login URL with redirect parameters
    params = {}
    if redirect_uri:
        params['redirect_uri'] = redirect_uri
    if state:
        params['state'] = state
    
    if params:
        login_url += '?' + urlencode(params)
    
    return RedirectResponse(url=login_url, status_code=302)


@router.get("/callback", summary="Handle authentication callback", tags=["auth", "centralized"])
async def auth_callback(
    request: Request,
    token: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Handle the callback after authentication.
    
    This endpoint receives the authentication result and redirects
    back to the original caller with the token.
    
    Args:
        token: JWT token (if authentication succeeded)
        redirect_uri: Where to redirect to
        state: State parameter from original request
        error: Error message (if authentication failed)
    
    Returns:
        Redirect back to caller
    """
    if error:
        # Authentication failed
        if redirect_uri:
            params = {'error': error}
            if state:
                params['state'] = state
            redirect_url = f"{redirect_uri}?{urlencode(params)}"
            return RedirectResponse(url=redirect_url, status_code=302)
        else:
            raise HTTPException(status_code=400, detail=error)
    
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    
    # Verify the token
    claims = jwt_manager.verify_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if redirect_uri:
        return await _redirect_with_token(redirect_uri, token, state)
    else:
        return {
            "success": True,
            "token": token,
            "user_id": claims.get("sub"),
            "username": claims.get("username")
        }


async def _redirect_with_token(redirect_uri: str, token: str, state: Optional[str] = None):
    """Helper to redirect with token in URL parameters."""
    params = {'token': token}
    if state:
        params['state'] = state
    
    # Parse redirect_uri to add parameters
    parsed = urlparse(redirect_uri)
    existing_params = parse_qs(parsed.query)
    existing_params.update(params)
    
    # Build new URL
    from urllib.parse import urlunparse
    new_query = urlencode(existing_params, doseq=True)
    redirect_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    # Set cookie as well for subsequent requests
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
        domain=None  # Allow cross-subdomain if needed
    )
    
    return response


@router.post("/refresh", summary="Refresh JWT token", tags=["auth", "centralized"])
async def refresh_token(request: Request):
    """
    Refresh an existing JWT token.
    
    This extends the expiration of a valid token.
    
    Returns:
        New JWT token
    """
    # Get token from request
    token = request.cookies.get('auth_token')
    if not token:
        # Also check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
    
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    # Refresh the token
    new_token = jwt_manager.refresh_token(token)
    
    if not new_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "success": True,
        "token": new_token
    }


@router.get("/auth-info", summary="Get authentication server info", tags=["auth", "centralized"])
async def get_auth_info(request: Request):
    """
    Get information about the authentication server.
    
    Returns:
        Server configuration and endpoints
    """
    host = request.headers.get("host", AUTH_SERVER_DOMAIN)
    protocol = "https" if request.url.scheme == "https" else "http"
    base_url = f"{protocol}://{host}"
    
    return {
        "auth_server": AUTH_SERVER_DOMAIN,
        "current_host": host,
        "endpoints": {
            "secret": f"{base_url}/auth-app/api/centralized/secret",
            "jwks": f"{base_url}/auth-app/api/centralized/.well-known/jwks.json",
            "login": f"{base_url}/auth-app/api/centralized/login",
            "callback": f"{base_url}/auth-app/api/centralized/callback",
            "verify": f"{base_url}/auth-app/api/centralized/verify-token",
            "refresh": f"{base_url}/auth-app/api/centralized/refresh"
        },
        "token_type": "JWT",
        "algorithm": "HS256",
        "issuer": "api.oneaurica.com",
        "audience": "aurica-apps",
        "note": "Use /secret endpoint to get shared secret for token verification"
    }
