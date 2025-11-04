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


@router.get("/", response_model=UserProfile, summary="Get user profile", tags=["users"])
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
    
    # Extract user_id from authenticated user data
    user_id = user_data.get('user_id')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session data")
    
    # Fetch user from passkey store
    user = passkey_store.get_user_by_id(user_id)
    
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


@router.put("/", response_model=UpdateProfileResponse, summary="Update user profile", tags=["users"])
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
    
    # Extract user_id from authenticated user data
    user_id = user_data.get('user_id')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session data")
    
    # Fetch user from passkey store
    user = passkey_store.get_user_by_id(user_id)
    
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
