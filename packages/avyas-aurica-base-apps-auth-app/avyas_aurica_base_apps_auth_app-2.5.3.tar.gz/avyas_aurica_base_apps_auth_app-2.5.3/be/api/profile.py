"""
User profile API endpoint.
"""
from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Import passkey store
import passkey_store as ps_module
passkey_store = ps_module.passkey_store

# Import session manager from auth middleware
try:
    from src.auth_middleware import session_manager
except ImportError:
    # Fallback for development
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
    from auth_middleware import session_manager

# Import authentication decorators from base
try:
    from src.auth_decorators import require_auth
except ImportError:
    def require_auth(func):
        return func


router = APIRouter()


class CredentialInfo(BaseModel):
    """Credential information model."""
    created_at: str


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str
    username: str
    email: str
    display_name: str
    role: str
    mobile_number: Optional[str] = None
    mobile_verified: bool = False
    created_at: str
    credentials: List[CredentialInfo] = []


class UpdateProfileRequest(BaseModel):
    """Update profile request model."""
    display_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None


class UpdateProfileResponse(BaseModel):
    """Update profile response model."""
    success: bool
    message: str
    user: UserProfile


@router.get("", response_model=UserProfile, summary="Get user profile", tags=["users"])
@require_auth
async def get_profile(request: Request):
    """
    Get current user's profile information.
    
    Returns:
        UserProfile with user information
    """
    # Get user from request state (already authenticated by middleware)
    user_data = getattr(request.state, 'user', None)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract user_id and username from authenticated user data
    user_id = user_data.get('user_id')
    username = user_data.get('username')
    
    print(f"🔍 Profile lookup - user_id: {user_id}, username: {username}")
    
    if not user_id and not username:
        raise HTTPException(status_code=401, detail="Invalid session data")
    
    # Check if we're running on the auth server or execution node
    import os
    auth_server_domain = os.getenv("AUTH_SERVER_DOMAIN", "api.oneaurica.com")
    is_auth_server = passkey_store.is_auth_server
    
    # If we're NOT the auth server, proxy to auth server
    if not is_auth_server:
        print(f"🔄 Not auth server, proxying profile request to {auth_server_domain}")
        import httpx
        
        # Get auth token from request
        auth_token = request.cookies.get('auth_token')
        if not auth_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                auth_token = auth_header.replace('Bearer ', '')
        
        if not auth_token:
            raise HTTPException(status_code=401, detail="No auth token found")
        
        # Proxy request to auth server
        protocol = "https" if "localhost" not in auth_server_domain else "http"
        auth_server_url = f"{protocol}://{auth_server_domain}/auth-app/api/profile"
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    auth_server_url,
                    headers={"Authorization": f"Bearer {auth_token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Auth server error: {response.text}"
                    )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Cannot reach auth server: {str(e)}")
    
    # We ARE the auth server, lookup locally
    print(f"✅ Auth server mode, looking up user locally")
    
    # Try to fetch user from passkey store by user_id first, then username
    user = passkey_store.get_user_by_id(user_id) if user_id else None
    print(f"🔍 Lookup by user_id result: {user is not None}")
    
    if not user and username:
        print(f"🔍 Trying lookup by username: {username}")
        user = passkey_store.get_user_by_username(username)
        print(f"🔍 Lookup by username result: {user is not None}")
        
        # Debug: print available usernames
        if not user:
            available_users = list(passkey_store._username_to_id.keys())
            print(f"🔍 Available usernames in store: {available_users}")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return user profile
    return UserProfile(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        mobile_number=user.mobile_number,
        mobile_verified=user.mobile_verified,
        created_at=user.created_at.isoformat(),
        credentials=[
            CredentialInfo(created_at=cred.created_at.isoformat())
            for cred in user.credentials
        ]
    )


@router.put("", response_model=UpdateProfileResponse, summary="Update user profile", tags=["users"])
@require_auth
async def update_profile(request: Request, profile: UpdateProfileRequest):
    """
    Update current user's profile information.
    
    Args:
        profile: Updated profile data
        
    Returns:
        Success response with updated data
    """
    # Get user from request state (already authenticated by middleware)
    user_data = getattr(request.state, 'user', None)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract user_id and username from authenticated user data
    user_id = user_data.get('user_id')
    username = user_data.get('username')
    
    if not user_id and not username:
        raise HTTPException(status_code=401, detail="Invalid session data")
    
    # Try to fetch user from passkey store by user_id first, then username
    user = passkey_store.get_user_by_id(user_id) if user_id else None
    
    if not user and username:
        user = passkey_store.get_user_by_username(username)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    if profile.display_name is not None:
        user.display_name = profile.display_name
    if profile.email is not None:
        user.email = profile.email
    if profile.mobile_number is not None:
        user.mobile_number = profile.mobile_number
    
    # Save changes
    passkey_store._save_to_storage()
    
    # Return updated profile
    return UpdateProfileResponse(
        success=True,
        message="Profile updated successfully",
        user=UserProfile(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            mobile_number=user.mobile_number,
            mobile_verified=user.mobile_verified,
            created_at=user.created_at.isoformat(),
            credentials=[
                CredentialInfo(created_at=cred.created_at.isoformat())
                for cred in user.credentials
            ]
        )
    )
