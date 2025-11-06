"""
Debug endpoint to check passkey store status.
"""
from fastapi import APIRouter
from typing import List
import sys
from pathlib import Path

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Now import passkey_store as a module
import passkey_store as ps_module
passkey_store = ps_module.passkey_store


router = APIRouter()


@router.get("/users", summary="List all registered users (debug)", tags=["debug"])
async def list_users():
    """
    Get a list of all registered users with their credentials.
    
    Returns:
        List of users with basic information
    """
    users = passkey_store.get_all_users()
    
    return {
        "total_users": len(users),
        "users": [
            {
                "user_id": user.user_id[:16] + "...",  # Truncate for display
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "credentials_count": len(user.credentials),
                "credentials": [
                    {
                        "device_type": cred.device_type,
                        "transports": cred.transports,
                        "created_at": cred.created_at.isoformat(),
                        "last_used": cred.last_used.isoformat() if cred.last_used else None
                    }
                    for cred in user.credentials
                ],
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]
    }


@router.get("/store-info", summary="Get passkey store information", tags=["debug"])
async def get_store_info():
    """
    Get information about the passkey store state.
    
    Returns:
        Store statistics
    """
    users = passkey_store.get_all_users()
    total_credentials = sum(len(user.credentials) for user in users)
    
    return {
        "store_type": "persistent-json",
        "data_file": str(passkey_store.users_file),
        "data_directory": str(passkey_store.data_dir),
        "file_exists": passkey_store.users_file.exists(),
        "total_users": len(users),
        "total_credentials": total_credentials,
        "usernames": [user.username for user in users],
        "note": "Data persists across server restarts."
    }
