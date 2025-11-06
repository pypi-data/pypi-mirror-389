"""
Passkey registration API endpoints for WebAuthn.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import secrets
import base64
import sys
import json
from pathlib import Path

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    AuthenticatorAttachment,
    PublicKeyCredentialDescriptor,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

# Now import passkey_store as a module
import passkey_store as ps_module
passkey_store = ps_module.passkey_store

# Import JWT utilities to check if we're on auth server
from jwt_utils import is_auth_server

# Import authentication decorators from base
try:
    from src.auth_decorators import public_endpoint
except ImportError:
    # Fallback if running in different context
    def public_endpoint(func):
        return func


router = APIRouter()

# Configuration
RP_NAME = "Aurica Auth App"

# Temporary storage for registration challenges
registration_challenges: dict = {}


def get_rp_id_and_origin(request: Request) -> tuple[str, str]:
    """Extract RP_ID and ORIGIN from the request headers."""
    host = request.headers.get("host", "")
    # Remove port if present (e.g., localhost:8000 -> localhost)
    rp_id = host.split(":")[0] if host else "localhost"
    
    # Determine protocol (check if request is secure)
    protocol = "https" if request.url.scheme == "https" else "http"
    origin = f"{protocol}://{host}"
    
    return rp_id, origin


class RegistrationStartRequest(BaseModel):
    """Request to start passkey registration."""
    username: str
    email: str
    display_name: str


class RegistrationStartResponse(BaseModel):
    """Response with registration options."""
    options: dict
    user_id: str


class RegistrationVerifyRequest(BaseModel):
    """Request to verify registration response."""
    user_id: str
    credential: dict


class RegistrationVerifyResponse(BaseModel):
    """Response after verifying registration."""
    success: bool
    message: str
    username: str


@router.post("/start", response_model=RegistrationStartResponse, summary="Start passkey registration", tags=["auth", "passkey"])
@public_endpoint
async def start_registration(registration_request: RegistrationStartRequest, request: Request):
    """
    Start the passkey registration process.
    
    IMPORTANT: Registration can ONLY happen on the centralized auth server.
    API execution providers should redirect users to the auth server.
    
    This generates registration options that the client will use to create
    a new passkey credential.
    
    Args:
        registration_request: User information for registration
        request: FastAPI request object
        
    Returns:
        Registration options to be passed to the WebAuthn API
    """
    # Check if we're on the auth server
    if not is_auth_server():
        raise HTTPException(
            status_code=403,
            detail="Registration can only be performed on the centralized auth server. "
                   "Please redirect to api.oneaurica.com for registration."
        )
    
    # Get dynamic RP_ID and ORIGIN from request
    rp_id, origin = get_rp_id_and_origin(request)
    
    # Check if user already exists
    existing_user = passkey_store.get_user_by_username(registration_request.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Generate a unique user ID (as string for storage, bytes for WebAuthn)
    user_id_bytes = secrets.token_bytes(32)
    user_id = base64.urlsafe_b64encode(user_id_bytes).decode('utf-8').rstrip('=')
    
    # Get existing credentials (empty for new user)
    exclude_credentials: List[PublicKeyCredentialDescriptor] = []
    
    # Generate registration options
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=RP_NAME,
        user_id=user_id_bytes,  # Use bytes for WebAuthn
        user_name=registration_request.username,
        user_display_name=registration_request.display_name,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            # Allow cross-device authentication (desktop can use mobile passkeys)
            # Not specifying authenticator_attachment allows both platform and cross-platform
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )
    
    # Store the challenge for verification
    registration_challenges[user_id] = {
        "challenge": options.challenge,
        "username": registration_request.username,
        "email": registration_request.email,
        "display_name": registration_request.display_name,
        "rp_id": rp_id,
        "origin": origin,
    }
    
    # Convert options to dict (options_to_json returns a JSON string)
    options_dict = json.loads(options_to_json(options))
    
    return RegistrationStartResponse(
        options=options_dict,
        user_id=user_id
    )


@router.post("/verify", response_model=RegistrationVerifyResponse, summary="Verify passkey registration", tags=["auth", "passkey"])
@public_endpoint
async def verify_registration(verify_request: RegistrationVerifyRequest):
    """
    Verify the passkey registration response from the client.
    
    This validates the credential created by the WebAuthn API and stores it.
    
    Args:
        verify_request: Registration response from the client
        
    Returns:
        Success confirmation
    """
    # Get the stored challenge
    challenge_data = registration_challenges.get(verify_request.user_id)
    if not challenge_data:
        raise HTTPException(status_code=400, detail="Invalid or expired registration session")
    
    # Get the stored RP_ID and ORIGIN from the challenge
    rp_id = challenge_data["rp_id"]
    origin = challenge_data["origin"]
    
    try:
        # Verify the registration response
        verification = verify_registration_response(
            credential=verify_request.credential,
            expected_challenge=challenge_data["challenge"],
            expected_origin=origin,
            expected_rp_id=rp_id,
        )
        
        # Create the user
        user = passkey_store.create_user(
            user_id=verify_request.user_id,
            username=challenge_data["username"],
            email=challenge_data["email"],
            display_name=challenge_data["display_name"]
        )
        
        # Detect device type from transports
        transports = verify_request.credential.get("response", {}).get("transports", [])
        device_type = "other"
        if "internal" in transports:
            device_type = "mobile"  # Platform authenticator (Touch ID, Face ID, etc.)
        elif "usb" in transports or "nfc" in transports or "ble" in transports:
            device_type = "desktop"  # External authenticator (security key)
        
        # Store the credential
        passkey_store.add_credential(
            user_id=verify_request.user_id,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            transports=transports,
            device_type=device_type,
            aaguid=verification.aaguid if hasattr(verification, 'aaguid') else None
        )
        
        # Clean up the challenge
        del registration_challenges[verify_request.user_id]
        
        return RegistrationVerifyResponse(
            success=True,
            message="Registration successful",
            username=user.username
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration verification failed: {str(e)}")


@router.get("/info", summary="Get registration endpoint info", tags=["auth", "passkey"])
@public_endpoint
async def get_registration_info(request: Request):
    """Get information about the registration endpoints."""
    rp_id, _ = get_rp_id_and_origin(request)
    return {
        "endpoints": {
            "/start": "Start passkey registration",
            "/verify": "Verify passkey registration"
        },
        "rp_id": rp_id,
        "rp_name": RP_NAME
    }
