"""
Admin user management API endpoint.
"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
_api_dir = Path(__file__).parent.parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Import authentication decorators from base
try:
    from src.auth_decorators import require_auth
except ImportError:
    # Fallback if running in different context
    def require_auth(func):
        return func

# Import passkey store
from passkey_store import passkey_store


router = APIRouter()


class User(BaseModel):
    """User model."""
    user_id: str
    username: str
    email: str
    display_name: str
    role: str
    mobile_number: Optional[str] = None
    mobile_verified: bool = False
    credential_count: int = 0
    created_at: str


class CreateUserRequest(BaseModel):
    """Create user request model."""
    username: str
    email: str
    display_name: str
    role: str = "user"
    mobile_number: Optional[str] = None


class CreateUserResponse(BaseModel):
    """Create user response model."""
    success: bool
    message: str
    user: User


class UpdateUserRequest(BaseModel):
    """Update user request model."""
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    mobile_number: Optional[str] = None
    mobile_verified: Optional[bool] = None


class UpdateUserResponse(BaseModel):
    """Update user response model."""
    success: bool
    message: str
    user: User


class DeleteUserResponse(BaseModel):
    """Delete user response model."""
    success: bool
    message: str


@router.get("/", response_model=List[User], summary="List all users", tags=["admin"])
@require_auth
async def list_users():
    """
    Get a list of all users in the system.
    
    Returns:
        List of User objects
    """
    users = passkey_store.get_all_users()
    return [
        User(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            mobile_number=user.mobile_number,
            mobile_verified=user.mobile_verified,
            credential_count=len(user.credentials),
            created_at=user.created_at.isoformat()
        )
        for user in users
    ]


@router.post("/", response_model=CreateUserResponse, summary="Create new user", tags=["admin"])
@require_auth
async def create_user(user_req: CreateUserRequest):
    """
    Create a new user in the system.
    
    Args:
        user_req: User data to create
        
    Returns:
        Success response with created user data
    """
    try:
        # Generate a user ID
        import secrets
        user_id = secrets.token_urlsafe(32)
        
        user = passkey_store.create_user(
            user_id=user_id,
            username=user_req.username,
            email=user_req.email,
            display_name=user_req.display_name,
            mobile_number=user_req.mobile_number,
            role=user_req.role
        )
        
        return CreateUserResponse(
            success=True,
            message="User created successfully",
            user=User(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                mobile_number=user.mobile_number,
                mobile_verified=user.mobile_verified,
                credential_count=0,
                created_at=user.created_at.isoformat()
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/{user_id}", response_model=UpdateUserResponse, summary="Update user", tags=["admin"])
@require_auth
async def update_user(user_id: str, update_req: UpdateUserRequest):
    """
    Update an existing user.
    
    Args:
        user_id: The ID of the user to update
        update_req: Fields to update
        
    Returns:
        Success response with updated user data
    """
    try:
        # Build update dict from non-None fields
        updates = {}
        if update_req.display_name is not None:
            updates['display_name'] = update_req.display_name
        if update_req.email is not None:
            updates['email'] = update_req.email
        if update_req.role is not None:
            updates['role'] = update_req.role
        if update_req.mobile_number is not None:
            updates['mobile_number'] = update_req.mobile_number
        if update_req.mobile_verified is not None:
            updates['mobile_verified'] = update_req.mobile_verified
        
        user = passkey_store.update_user(user_id, **updates)
        
        return UpdateUserResponse(
            success=True,
            message="User updated successfully",
            user=User(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                mobile_number=user.mobile_number,
                mobile_verified=user.mobile_verified,
                credential_count=len(user.credentials),
                created_at=user.created_at.isoformat()
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/{user_id}", response_model=DeleteUserResponse, summary="Delete user", tags=["admin"])
@require_auth
async def delete_user(user_id: str):
    """
    Delete a user from the system.
    
    Args:
        user_id: The ID of the user to delete
        
    Returns:
        Success response
    """
    try:
        success = passkey_store.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return DeleteUserResponse(
            success=True,
            message=f"User {user_id} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
