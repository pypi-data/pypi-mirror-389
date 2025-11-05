"""
Test endpoint to verify credential lookup.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import base64
import sys
from pathlib import Path

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

import passkey_store as ps_module
passkey_store = ps_module.passkey_store

router = APIRouter()


class TestCredentialRequest(BaseModel):
    credential_id_base64: str


@router.post("/test-credential", summary="Test credential lookup", tags=["debug"])
async def test_credential_lookup(request: TestCredentialRequest):
    """
    Test if a credential ID can be found in the store.
    """
    try:
        # Decode the credential ID
        credential_id = base64.urlsafe_b64decode(request.credential_id_base64 + '==')
        
        # Find user
        user = passkey_store.get_user_by_credential_id(credential_id)
        
        # Get all users for comparison
        all_users = passkey_store.get_all_users()
        
        result = {
            "credential_id_base64": request.credential_id_base64,
            "credential_id_length": len(credential_id),
            "user_found": user is not None,
            "username": user.username if user else None,
            "total_users": len(all_users),
            "all_credentials": []
        }
        
        # List all credentials
        for u in all_users:
            for c in u.credentials:
                cred_id_b64 = base64.urlsafe_b64encode(c.credential_id).decode('utf-8').rstrip('=')
                result["all_credentials"].append({
                    "username": u.username,
                    "credential_id_base64": cred_id_b64,
                    "device_type": c.device_type,
                    "transports": c.transports,
                    "matches": c.credential_id == credential_id
                })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/list-credentials", summary="List all stored credentials", tags=["debug"])
async def list_all_credentials():
    """
    List all credentials in the store.
    """
    all_users = passkey_store.get_all_users()
    
    credentials = []
    for user in all_users:
        for cred in user.credentials:
            cred_id_b64 = base64.urlsafe_b64encode(cred.credential_id).decode('utf-8').rstrip('=')
            credentials.append({
                "username": user.username,
                "user_id": user.user_id[:16] + "...",
                "credential_id_base64": cred_id_b64,
                "device_type": cred.device_type,
                "transports": cred.transports,
                "sign_count": cred.sign_count,
                "created_at": cred.created_at.isoformat(),
                "last_used": cred.last_used.isoformat() if cred.last_used else None
            })
    
    return {
        "total_credentials": len(credentials),
        "credentials": credentials
    }
