"""
Persistent storage for user credentials and passkey data using JSON files.
Data is stored in the data/ folder parallel to apps/ (local) or S3 (production).
ONLY loads user data on the centralized auth server (api.oneaurica.com).
Other hosts just verify JWT tokens and don't need user database access.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import base64
import os
from pathlib import Path
import sys

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

import s3_storage
S3Storage = s3_storage.S3Storage
is_serverless_environment = s3_storage.is_serverless_environment

# Check if we're running on the centralized auth server
def is_auth_server():
    """Check if this instance is the centralized auth server."""
    # Check explicit environment variable first
    is_auth = os.getenv("IS_AUTH_SERVER", "").lower() in ("true", "1", "yes")
    if os.getenv("IS_AUTH_SERVER"):
        return is_auth
    
    # Otherwise, check if we're running in production (not localhost)
    auth_server_domain = os.getenv("AUTH_SERVER_DOMAIN", "")
    
    # If AUTH_SERVER_DOMAIN is not set or contains localhost/127.0.0.1, we're NOT the auth server
    if not auth_server_domain or "localhost" in auth_server_domain or "127.0.0.1" in auth_server_domain:
        return False
    
    # If AUTH_SERVER_DOMAIN is set to a production domain, we ARE the auth server
    return True


class PasskeyCredential(BaseModel):
    """Model for storing passkey credential data."""
    credential_id: bytes
    public_key: bytes
    sign_count: int
    transports: Optional[List[str]] = None
    created_at: datetime = datetime.utcnow()
    last_used: Optional[datetime] = None
    device_type: Optional[str] = None  # 'mobile', 'desktop', or 'other'
    aaguid: Optional[bytes] = None  # Authenticator AAGUID for tracking
    
    class Config:
        arbitrary_types_allowed = True


class User(BaseModel):
    """User model with passkey credentials."""
    user_id: str
    username: str
    email: str
    display_name: str
    role: str = "user"  # Default role: user, admin, or other custom roles
    mobile_number: Optional[str] = None
    mobile_verified: bool = False
    credentials: List[PasskeyCredential] = []
    created_at: datetime = datetime.utcnow()


class PasskeyStore:
    """Persistent storage for users and their passkey credentials."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        # Only use S3 storage on the centralized auth server
        self.is_auth_server = is_auth_server()
        self.use_s3 = self.is_auth_server
        
        if self.use_s3:
            self.s3_storage = S3Storage()
            print(f"🔐 PasskeyStore: Running as AUTH SERVER - will load user data from S3")
        else:
            self.s3_storage = None
            print(f"🔓 PasskeyStore: Running as regular host - no user data needed (JWT verification only)")
        
        # In-memory indices for fast lookup
        self._users: Dict[str, User] = {}
        self._username_to_id: Dict[str, str] = {}
        self._mobile_to_id: Dict[str, str] = {}
        self._credential_to_user: Dict[bytes, str] = {}
        
        # Load existing data from S3 only if we're the auth server
        if self.use_s3:
            self._load_from_storage()
    
    def _load_from_storage(self):
        """Load users from S3 storage (only on auth server)."""
        if not self.use_s3:
            return
            
        data = self.s3_storage.load_json('users.json')
        
        if not data:
            print(f"No existing users found in S3. Starting fresh.")
            return
        
        try:
            # Reconstruct users
            for user_data in data.get('users', []):
                # Add default role if missing (backward compatibility)
                if 'role' not in user_data:
                    user_data['role'] = 'user'
                
                # Decode bytes fields in credentials
                credentials = []
                for cred_data in user_data.get('credentials', []):
                    # Decode base64 encoded bytes
                    cred_data['credential_id'] = base64.b64decode(cred_data['credential_id'])
                    cred_data['public_key'] = base64.b64decode(cred_data['public_key'])
                    if cred_data.get('aaguid'):
                        cred_data['aaguid'] = base64.b64decode(cred_data['aaguid'])
                    
                    # Parse datetime strings
                    cred_data['created_at'] = datetime.fromisoformat(cred_data['created_at'])
                    if cred_data.get('last_used'):
                        cred_data['last_used'] = datetime.fromisoformat(cred_data['last_used'])
                    
                    credentials.append(PasskeyCredential(**cred_data))
                
                # Parse datetime
                user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                user_data['credentials'] = credentials
                
                user = User(**user_data)
                self._users[user.user_id] = user
                self._username_to_id[user.username] = user.user_id
                if user.mobile_number:
                    self._mobile_to_id[user.mobile_number] = user.user_id
                
                # Index credentials
                for cred in user.credentials:
                    self._credential_to_user[cred.credential_id] = user.user_id
            
            print(f"Loaded {len(self._users)} users from S3")
            print(f"Usernames: {list(self._username_to_id.keys())}")
            
        except Exception as e:
            print(f"Error loading users from S3: {e}")
            print("Starting with empty user store.")
    
    def _save_to_storage(self):
        """Save users to S3 storage (only on auth server)."""
        if not self.use_s3:
            print("⚠️  Not on auth server - cannot save user data")
            return
            
        try:
            # Convert users to serializable format
            users_data = []
            for user in self._users.values():
                user_dict = user.dict()
                
                # Convert datetime to ISO format
                user_dict['created_at'] = user.created_at.isoformat()
                
                # Convert bytes to base64 strings in credentials
                credentials_data = []
                for cred in user.credentials:
                    cred_dict = cred.dict()
                    cred_dict['credential_id'] = base64.b64encode(cred.credential_id).decode('utf-8')
                    cred_dict['public_key'] = base64.b64encode(cred.public_key).decode('utf-8')
                    if cred.aaguid:
                        cred_dict['aaguid'] = base64.b64encode(cred.aaguid).decode('utf-8')
                    cred_dict['created_at'] = cred.created_at.isoformat()
                    if cred.last_used:
                        cred_dict['last_used'] = cred.last_used.isoformat()
                    credentials_data.append(cred_dict)
                
                user_dict['credentials'] = credentials_data
                users_data.append(user_dict)
            
            # Save to S3
            self.s3_storage.save_json('users.json', {'users': users_data})
            print(f"Saved {len(self._users)} users to S3")
            
        except Exception as e:
            print(f"Error saving users to S3: {e}")
    
    @property
    def users(self):
        """Property to access users dict (for compatibility)."""
        return self._users
    
    def create_user(self, user_id: str, username: str, email: str, display_name: str, 
                    mobile_number: Optional[str] = None, role: str = "user") -> User:
        """Create a new user."""
        if username in self._username_to_id:
            raise ValueError(f"User {username} already exists")
        
        if mobile_number and mobile_number in self._mobile_to_id:
            raise ValueError(f"Mobile number {mobile_number} already registered")
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            display_name=display_name,
            mobile_number=mobile_number,
            role=role
        )
        self._users[user_id] = user
        self._username_to_id[username] = user_id
        if mobile_number:
            self._mobile_to_id[mobile_number] = user_id
        
        # Save to disk
        self._save_to_storage()
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        user_id = self._username_to_id.get(username)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def get_user_by_mobile(self, mobile_number: str) -> Optional[User]:
        """Get user by mobile number."""
        user_id = self._mobile_to_id.get(mobile_number)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def get_user_by_credential_id(self, credential_id: bytes) -> Optional[User]:
        """Get user by credential ID."""
        user_id = self._credential_to_user.get(credential_id)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def add_credential(
        self,
        user_id: str,
        credential_id: bytes,
        public_key: bytes,
        sign_count: int,
        transports: Optional[List[str]] = None,
        device_type: Optional[str] = None,
        aaguid: Optional[bytes] = None
    ) -> None:
        """Add a passkey credential to a user."""
        user = self._users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        credential = PasskeyCredential(
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            transports=transports,
            device_type=device_type,
            aaguid=aaguid
        )
        
        user.credentials.append(credential)
        self._credential_to_user[credential_id] = user_id
        
        # Save to disk
        self._save_to_storage()
    
    def get_credential(self, user_id: str, credential_id: bytes) -> Optional[PasskeyCredential]:
        """Get a specific credential for a user."""
        user = self._users.get(user_id)
        if not user:
            return None
        
        for cred in user.credentials:
            if cred.credential_id == credential_id:
                return cred
        return None
    
    def update_credential_sign_count(self, user_id: str, credential_id: bytes, sign_count: int) -> None:
        """Update the sign count for a credential."""
        credential = self.get_credential(user_id, credential_id)
        if credential:
            credential.sign_count = sign_count
            credential.last_used = datetime.utcnow()
            
            # Save to disk
            self._save_to_storage()
    
    def get_all_users(self) -> List[User]:
        """Get all users (for admin purposes)."""
        return list(self._users.values())
    
    def update_user(self, user_id: str, **kwargs) -> User:
        """Update user fields."""
        user = self._users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Update allowed fields
        allowed_fields = ['display_name', 'email', 'mobile_number', 'mobile_verified', 'role']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        # Update indices if username changed (not allowed currently for simplicity)
        # Update mobile index if mobile changed
        if 'mobile_number' in kwargs:
            # Remove old mobile from index
            old_mobile = user.mobile_number
            if old_mobile and old_mobile in self._mobile_to_id:
                del self._mobile_to_id[old_mobile]
            # Add new mobile to index
            if kwargs['mobile_number']:
                self._mobile_to_id[kwargs['mobile_number']] = user_id
        
        self._save_to_storage()
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        user = self._users.get(user_id)
        if not user:
            return False
        
        # Remove from all indices
        if user.username in self._username_to_id:
            del self._username_to_id[user.username]
        if user.mobile_number and user.mobile_number in self._mobile_to_id:
            del self._mobile_to_id[user.mobile_number]
        
        # Remove credential mappings
        for cred in user.credentials:
            if cred.credential_id in self._credential_to_user:
                del self._credential_to_user[cred.credential_id]
        
        # Remove user
        del self._users[user_id]
        
        self._save_to_storage()
        return True
    
    def update_user_role(self, user_id: str, role: str) -> User:
        """Update user role specifically."""
        return self.update_user(user_id, role=role)


# Global store instance
passkey_store = PasskeyStore()
