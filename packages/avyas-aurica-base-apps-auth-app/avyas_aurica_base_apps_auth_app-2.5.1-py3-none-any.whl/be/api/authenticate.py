"""
Passkey authentication API endpoints for WebAuthn.
"""
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import base64
import sys
import json
import asyncio
from pathlib import Path

from webauthn import (
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Now import passkey_store as a module
import passkey_store as ps_module
passkey_store = ps_module.passkey_store

# Import JWT utilities
from jwt_utils import jwt_manager, is_auth_server

# Import session manager from auth middleware
try:
    from src.auth_middleware import session_manager
except ImportError:
    # Fallback for development
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
    from auth_middleware import session_manager


router = APIRouter()

# Temporary storage for authentication challenges
authentication_challenges: dict = {}

# Temporary storage for QR code sessions
qr_sessions: dict = {}  # {session_id: {"created_at": datetime, "authenticated": bool, "user_data": dict}}


def get_rp_id_and_origin(request: Request) -> tuple[str, str]:
    """Extract RP_ID and ORIGIN from the request headers."""
    host = request.headers.get("host", "")
    # Remove port if present (e.g., localhost:8000 -> localhost)
    rp_id = host.split(":")[0] if host else "localhost"
    
    # Determine protocol (check if request is secure)
    protocol = "https" if request.url.scheme == "https" else "http"
    origin = f"{protocol}://{host}"
    
    return rp_id, origin


class AuthenticationStartRequest(BaseModel):
    """Request to start passkey authentication."""
    username: Optional[str] = None  # Optional for discoverable credentials


class AuthenticationStartResponse(BaseModel):
    """Response with authentication options."""
    options: dict
    session_id: str


class AuthenticationVerifyRequest(BaseModel):
    """Request to verify authentication response."""
    session_id: str
    credential: dict


class AuthenticationVerifyResponse(BaseModel):
    """Response after verifying authentication."""
    success: bool
    message: str
    username: str
    user_id: str
    token: str


@router.post("/start", response_model=AuthenticationStartResponse, summary="Start passkey authentication", tags=["auth", "passkey"])
async def start_authentication(auth_request: AuthenticationStartRequest, request: Request):
    """
    Start the passkey authentication process.
    
    IMPORTANT: Authentication can ONLY happen on the centralized auth server.
    API execution providers should redirect users to the auth server.
    
    This generates authentication options that the client will use to
    authenticate with an existing passkey.
    
    Args:
        auth_request: Optional username for authentication
        request: FastAPI request object
        
    Returns:
        Authentication options to be passed to the WebAuthn API
    """
    # Get dynamic RP_ID and ORIGIN from request
    rp_id, origin = get_rp_id_and_origin(request)
    
    allow_credentials: List[PublicKeyCredentialDescriptor] = []
    
    # If username is provided, get their credentials
    if auth_request.username:
        user = passkey_store.get_user_by_username(auth_request.username)
        if user and user.credentials:
            allow_credentials = [
                PublicKeyCredentialDescriptor(
                    id=cred.credential_id,
                    transports=cred.transports,
                )
                for cred in user.credentials
            ]
    
    # Generate authentication options
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    
    # Create a session ID
    session_id = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Store the challenge for verification
    authentication_challenges[session_id] = {
        "challenge": options.challenge,
        "username": auth_request.username,
        "rp_id": rp_id,
        "origin": origin,
    }
    
    # Convert options to dict (options_to_json returns a JSON string)
    options_dict = json.loads(options_to_json(options))
    
    return AuthenticationStartResponse(
        options=options_dict,
        session_id=session_id
    )


@router.post("/verify", response_model=AuthenticationVerifyResponse, summary="Verify passkey authentication", tags=["auth", "passkey"])
async def verify_authentication(verify_request: AuthenticationVerifyRequest, response: Response):
    """
    Verify the passkey authentication response from the client.
    
    IMPORTANT: Authentication can ONLY happen on the centralized auth server.
    This endpoint generates JWT tokens which should only be done on the auth server.
    
    This validates the authentication assertion and logs the user in.
    
    Args:
        verify_request: Authentication response from the client
        response: FastAPI response object for setting cookies
        
    Returns:
        Success confirmation with user info and session token
    """
    # Get the stored challenge
    challenge_data = authentication_challenges.get(verify_request.session_id)
    if not challenge_data:
        raise HTTPException(status_code=400, detail="Invalid or expired authentication session")
    
    # Get the stored RP_ID and ORIGIN from the challenge
    rp_id = challenge_data["rp_id"]
    origin = challenge_data["origin"]
    
    try:
        # Get the credential ID from the response
        credential_id_b64 = verify_request.credential.get("id")
        if not credential_id_b64:
            raise HTTPException(status_code=400, detail="Missing credential ID")
        
        # Decode the credential ID (add padding if needed)
        # Base64 strings must be a multiple of 4 characters
        padding = (4 - len(credential_id_b64) % 4) % 4
        credential_id = base64.urlsafe_b64decode(credential_id_b64 + '=' * padding)
        
        # Debug logging
        print(f"\n=== Authentication Verify Debug ===")
        print(f"Credential ID (base64): {credential_id_b64[:20]}...")
        print(f"Credential ID (bytes length): {len(credential_id)}")
        
        # Check all users and their credentials
        all_users = passkey_store.get_all_users()
        print(f"Total users in store: {len(all_users)}")
        for u in all_users:
            print(f"  User: {u.username}, Credentials: {len(u.credentials)}")
            for i, c in enumerate(u.credentials):
                cred_id_b64 = base64.urlsafe_b64encode(c.credential_id).decode('utf-8').rstrip('=')
                match = c.credential_id == credential_id
                print(f"    Cred {i}: {cred_id_b64[:20]}... Match: {match}")
        
        # Find the user by credential ID
        user = passkey_store.get_user_by_credential_id(credential_id)
        if not user:
            print(f"ERROR: User not found for credential ID")
            print(f"Available usernames: {[u.username for u in all_users]}")
            raise HTTPException(
                status_code=404, 
                detail="User not found for this credential. The passkey may not be registered on this device."
            )
        
        print(f"Found user: {user.username}")
        
        # Get the credential
        credential = passkey_store.get_credential(user.user_id, credential_id)
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        # Verify the authentication response
        verification = verify_authentication_response(
            credential=verify_request.credential,
            expected_challenge=challenge_data["challenge"],
            expected_origin=origin,
            expected_rp_id=rp_id,
            credential_public_key=credential.public_key,
            credential_current_sign_count=credential.sign_count,
        )
        
        # Update the sign count
        passkey_store.update_credential_sign_count(
            user.user_id,
            credential_id,
            verification.new_sign_count
        )
        
        # Create a JWT token for cross-domain authentication
        jwt_token = jwt_manager.create_token(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            metadata={
                'login_time': str(verification.new_sign_count),
                'device_type': credential.device_type if hasattr(credential, 'device_type') else 'unknown'
            }
        )
        
        # Also create a session using the session manager for backward compatibility
        # Use the JWT token as the session key so lookups work
        session_token = session_manager.create_session(
            user_id=user.user_id,
            username=user.username,
            metadata={
                'login_time': str(verification.new_sign_count),
                'role': user.role
            },
            token=jwt_token  # Use JWT token as session key
        )
        
        # Set the authentication cookie with JWT token
        response.set_cookie(
            key="auth_token",
            value=jwt_token,  # Use JWT token instead of session token
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * 7  # 7 days
        )
        
        # Clean up the challenge
        del authentication_challenges[verify_request.session_id]
        
        # Auto-register execution node with cloud (non-blocking)
        # This ensures tunnel connects immediately after login
        try:
            import sys
            from pathlib import Path
            dt_path = Path(__file__).parent.parent.parent.parent / "digital-twin" / "be"
            if str(dt_path) not in sys.path:
                sys.path.insert(0, str(dt_path))
            from auto_register import register_execution_node
            
            # Save auth token for automatic reconnection on server restart
            base_be_path = Path(__file__).parent.parent.parent.parent / "aurica-base-be"
            if str(base_be_path) not in sys.path:
                sys.path.insert(0, str(base_be_path))
            from src.persistent_auth import save_auth_token
            save_auth_token(user.user_id, jwt_token)
            
            # Start tunnel immediately and keep it running
            asyncio.create_task(register_execution_node(user.user_id, jwt_token))
            print(f"🔗 Auto-establishing tunnel for {user.username}")
            
        except Exception as e:
            print(f"⚠️  Could not auto-establish tunnel: {e}")
        
        return AuthenticationVerifyResponse(
            success=True,
            message="Authentication successful",
            username=user.username,
            user_id=user.user_id,
            token=jwt_token  # Return JWT token to client
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication verification failed: {str(e)}")


@router.get("/info", summary="Get authentication endpoint info", tags=["auth", "passkey"])
async def get_authentication_info(request: Request):
    """Get information about the authentication endpoints."""
    rp_id, _ = get_rp_id_and_origin(request)
    return {
        "endpoints": {
            "/start": "Start passkey authentication",
            "/verify": "Verify passkey authentication",
            "/logout": "Logout and invalidate session",
            "/current-user": "Get current authenticated user"
        },
        "rp_id": rp_id,
        "supports_discoverable_credentials": True
    }


@router.post("/logout", summary="Logout user", tags=["auth"])
async def logout(request: Request, response: Response):
    """
    Logout the current user by invalidating their session.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object for clearing cookies
        
    Returns:
        Success confirmation
    """
    # Get token from request
    token = request.cookies.get('auth_token')
    if not token:
        # Also check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
    
    if token:
        # Invalidate the session
        session_manager.invalidate_session(token)
    
    # Clear the cookie
    response.delete_cookie(key="auth_token")
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.get("/current-user", summary="Get current user", tags=["auth"])
async def get_current_user_info(request: Request):
    """
    Get information about the currently authenticated user.
    This is a PUBLIC endpoint that returns 401 if not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User information or error if not authenticated
    """
    # Try to get user from request state (set by middleware if path is protected)
    user_data = getattr(request.state, 'user', None)
    
    # If not in state, manually check authentication (for public endpoint case)
    if not user_data:
        # Get token manually
        token = request.cookies.get('auth_token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
        
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Try to verify token using the middleware's helper
        from src.auth_middleware import get_current_user as middleware_get_user
        user_data = await middleware_get_user(request)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get role from user metadata
    role = user_data.get('metadata', {}).get('role', 'user')
    
    # Get token from request for returning it
    token = request.cookies.get('auth_token')
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
    
    return {
        "authenticated": True,
        "user_id": user_data['user_id'],
        "username": user_data['username'],
        "role": role,
        "token": token,  # Return the JWT token for redirect flow
        "session_created": user_data.get('created_at', datetime.utcnow()).isoformat() if hasattr(user_data.get('created_at'), 'isoformat') else str(user_data.get('created_at', '')),
        "last_accessed": user_data.get('last_accessed', datetime.utcnow()).isoformat() if hasattr(user_data.get('last_accessed'), 'isoformat') else str(user_data.get('last_accessed', ''))
    }


@router.post("/create-qr-session", summary="Create QR code login session", tags=["auth", "qr"])
async def create_qr_session(request: Request):
    """
    Create a QR code session for scan-to-login on desktop.
    
    Returns a session_id and qr_data that can be used to generate a QR code.
    The QR code contains a URL that mobile devices can scan to authenticate.
    """
    # Generate unique session ID
    session_id = secrets.token_urlsafe(32)
    
    # Get the auth server URL
    host = request.headers.get("host", "")
    protocol = "https" if request.url.scheme == "https" else "http"
    auth_url = f"{protocol}://{host}"
    
    # Create QR data (URL that mobile app will open)
    qr_data = f"{auth_url}/auth-app/api/authenticate/qr-authenticate?session_id={session_id}"
    
    # Store session
    qr_sessions[session_id] = {
        "created_at": datetime.utcnow(),
        "authenticated": False,
        "user_data": None,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)  # 5 minute expiry
    }
    
    return {
        "session_id": session_id,
        "qr_data": qr_data
    }


@router.get("/qr-authenticate", summary="Authenticate via QR code scan", tags=["auth", "qr"])
async def qr_authenticate(session_id: str, request: Request):
    """
    Endpoint that mobile device hits after scanning QR code.
    If user is already authenticated on mobile, complete the desktop login.
    Otherwise, redirect to login page.
    """
    # Check if session exists and is valid
    if session_id not in qr_sessions:
        raise HTTPException(status_code=404, detail="QR session not found or expired")
    
    session = qr_sessions[session_id]
    
    # Check if session has expired
    if datetime.utcnow() > session["expires_at"]:
        del qr_sessions[session_id]
        raise HTTPException(status_code=410, detail="QR session expired")
    
    # Check if user is already authenticated on mobile
    try:
        # Get token from request
        token = request.cookies.get('auth_token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
        
        if token:
            # Verify token
            from src.auth_middleware import get_current_user as middleware_get_user
            user_data = await middleware_get_user(request)
            
            if user_data:
                # User is authenticated, complete desktop login
                # Generate new token for desktop
                new_token = jwt_manager.create_token(
                    user_id=user_data['user_id'],
                    username=user_data['username'],
                    metadata=user_data.get('metadata', {})
                )
                
                # Store user data in session
                session["authenticated"] = True
                session["user_data"] = {
                    "user_id": user_data['user_id'],
                    "username": user_data['username'],
                    "token": new_token
                }
                
                return JSONResponse({
                    "success": True,
                    "message": "Authentication successful! You can close this window."
                })
    except Exception as e:
        print(f"QR auth error: {e}")
    
    # User not authenticated, redirect to login page with return URL
    host = request.headers.get("host", "")
    protocol = "https" if request.url.scheme == "https" else "http"
    return_url = f"{protocol}://{host}/auth-app/api/authenticate/qr-authenticate?session_id={session_id}"
    
    redirect_url = f"{protocol}://{host}/auth-app/static/index.html?qr_session={session_id}&return_url={return_url}"
    
    return JSONResponse({
        "authenticated": False,
        "redirect_url": redirect_url,
        "message": "Please log in to complete desktop authentication"
    }, headers={
        "Location": redirect_url
    }, status_code=302)


@router.get("/check-qr-session/{session_id}", summary="Check QR session status", tags=["auth", "qr"])
async def check_qr_session(session_id: str):
    """
    Check if a QR code session has been authenticated.
    Desktop polls this endpoint to check if mobile has completed auth.
    """
    if session_id not in qr_sessions:
        raise HTTPException(status_code=404, detail="QR session not found or expired")
    
    session = qr_sessions[session_id]
    
    # Check if session has expired
    if datetime.utcnow() > session["expires_at"]:
        del qr_sessions[session_id]
        raise HTTPException(status_code=410, detail="QR session expired")
    
    if session["authenticated"]:
        # Clean up session
        user_data = session["user_data"]
        del qr_sessions[session_id]
        
        return {
            "authenticated": True,
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "token": user_data["token"]
        }
    
    return {
        "authenticated": False
    }
