"""
JWT token generation and verification utilities for decentralized authentication.
Uses HMAC-based JWT (HS256) with shared secret - no key management needed!
Each host can verify tokens using the shared secret from centralized auth server.
ONLY generates tokens on the centralized auth server (api.oneaurica.com).
Other hosts just verify tokens via JWKS.
"""
import jwt
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add the auth-app api directory to path for imports
_api_dir = Path(__file__).parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

import s3_storage

# Check if we're running on the centralized auth server
def is_auth_server():
    """
    Check if this instance is the centralized auth server.
    
    The auth server is the ONLY place where:
    - Users can register accounts
    - Users can login
    - JWT tokens are GENERATED and SIGNED
    
    All other servers are API execution providers that:
    - Verify tokens using JWKS from the auth server
    - Never generate tokens themselves
    
    Returns:
        True if this is the auth server, False if API execution provider
    """
    # Explicit override via environment variable
    is_auth_env = os.getenv("IS_AUTH_SERVER", "").lower()
    if is_auth_env in ("true", "1", "yes"):
        return True
    if is_auth_env in ("false", "0", "no"):
        return False
    
    # Auto-detect: If AUTH_SERVER_DOMAIN doesn't contain localhost, 
    # assume we're an API execution provider (NOT the auth server)
    # The auth server must explicitly set IS_AUTH_SERVER=true
    auth_server_domain = os.getenv("AUTH_SERVER_DOMAIN", "api.oneaurica.com")
    
    # For localhost testing: assume IS the auth server
    if "localhost" in auth_server_domain or "127.0.0.1" in auth_server_domain:
        return True
    
    # For production: must explicitly set IS_AUTH_SERVER=true
    # Default to False (API execution provider)
    return False


class JWTManager:
    """
    Manages JWT token generation and verification with HMAC (HS256).
    
    Architecture:
    - ONE Auth Server (IS_AUTH_SERVER=true): Generates and signs tokens
    - Multiple API Execution Providers: Verify tokens using JWKS
    
    The auth server:
    - Loads/generates JWT_SECRET_KEY
    - Signs tokens with this secret
    - Exposes JWKS endpoint with the secret
    
    API execution providers:
    - Fetch JWKS from auth server
    - Verify tokens using the public key from JWKS
    - Never generate tokens themselves
    """
    
    def __init__(self):
        """Initialize JWT manager with shared secret."""
        self.is_auth_server = is_auth_server()
        self.storage = s3_storage.S3Storage() if self.is_auth_server else None
        self.secret_key = None
        self.auth_server_domain = os.getenv("AUTH_SERVER_DOMAIN", "api.oneaurica.com")
        
        if self.is_auth_server:
            print("=" * 60)
            print("🔐 JWTManager: Running as CENTRALIZED AUTH SERVER")
            print("   This is the ONLY place where:")
            print("   - Users can register accounts")
            print("   - Users can login") 
            print("   - JWT tokens are GENERATED and SIGNED")
            print("=" * 60)
            self._load_or_generate_secret()
        else:
            print("=" * 60)
            print("🔓 JWTManager: Running as API EXECUTION PROVIDER")
            print("   This server will:")
            print("   - Redirect users to auth server for login")
            print("   - Verify tokens using JWKS from auth server")
            print("   - Execute APIs for authenticated users")
            print("   - NEVER generate tokens itself")
            print("=" * 60)
            # Non-auth servers fetch the secret from auth server via JWKS
            self._fetch_secret_from_auth_server()
    
    def _load_or_generate_secret(self):
        """Load existing secret from storage or generate new one (only on auth server)."""
        if not self.is_auth_server:
            return
            
        # First try environment variable (for dynamic secrets)
        env_secret = os.getenv('JWT_SECRET_KEY')
        if env_secret:
            self.secret_key = env_secret
            print("✅ Using JWT secret from environment variable JWT_SECRET_KEY")
            print(f"   Secret key (first 8 chars): {env_secret[:8]}...")
            return
        
        try:
            # Try to load existing secret from storage
            print("🔑 Loading JWT secret from S3 storage...")
            secret_data = self.storage.load_json('jwt_secret.json')
            
            if secret_data and 'secret_key' in secret_data:
                self.secret_key = secret_data['secret_key']
                created_at = secret_data.get('created_at', 'unknown')
                print(f"✅ Loaded existing JWT secret from S3 storage")
                print(f"   Secret key (first 8 chars): {self.secret_key[:8]}...")
                print(f"   Created at: {created_at}")
                print(f"   Algorithm: {secret_data.get('algorithm', 'HS256')}")
            else:
                raise ValueError("Secret data incomplete")
                
        except Exception as e:
            print(f"⚠️  Could not load secret from S3: {e}")
            print(f"⚠️  Attempting to generate and save new secret...")
            
            try:
                # Try to generate and save a new secret
                self._generate_new_secret()
                print(f"✅ Successfully generated and saved new JWT secret to S3")
                print(f"   ⚠️  WARNING: Old tokens signed with previous secret will be INVALID!")
                print(f"   ⚠️  All server instances must restart to use the new secret")
            except Exception as save_error:
                print(f"❌ Failed to save new secret to S3: {save_error}")
                print("🔑 Using temporary in-memory JWT secret...")
                # Generate temporary secret - won't be persisted if S3 is having issues
                self.secret_key = secrets.token_urlsafe(32)
                print(f"⚠️  Using temporary JWT secret - tokens won't work across restarts!")
                print(f"💡 Set JWT_SECRET_KEY environment variable to use a fixed secret")
    
    def _fetch_secret_from_auth_server(self):
        """Fetch JWT secret from centralized auth server via JWKS (only on API execution providers)."""
        if self.is_auth_server:
            return
            
        try:
            import requests
            
            # Try to fetch JWKS from auth server
            jwks_url = f"https://{self.auth_server_domain}/auth-app/api/centralized_auth/.well-known/jwks.json"
            print(f"🔑 Fetching JWT secret from auth server: {jwks_url}")
            
            response = requests.get(jwks_url, timeout=5)
            response.raise_for_status()
            
            jwks = response.json()
            
            # Extract the secret key from JWKS (for HMAC/HS256)
            if 'keys' in jwks and len(jwks['keys']) > 0:
                key_data = jwks['keys'][0]
                if key_data.get('kty') == 'oct' and key_data.get('alg') == 'HS256':
                    self.secret_key = key_data.get('k')
                    print(f"✅ Successfully fetched JWT secret from auth server")
                    print(f"   Secret key (first 8 chars): {self.secret_key[:8]}...")
                    print(f"   Algorithm: {key_data.get('alg')}")
                else:
                    print(f"⚠️  Unexpected key type in JWKS: {key_data.get('kty')}")
            else:
                print(f"⚠️  No keys found in JWKS response")
                
        except Exception as e:
            print(f"⚠️  Failed to fetch JWT secret from auth server: {e}")
            print(f"   Will not be able to verify JWT tokens!")
            print(f"   Make sure {self.auth_server_domain} is accessible")

    
    def _generate_new_secret(self):
        """Generate a new shared secret and save to storage (only on auth server)."""
        if not self.is_auth_server:
            return
            
        # Generate a secure random secret (256 bits)
        self.secret_key = secrets.token_urlsafe(32)
        
        # Save to storage
        secret_data = {
            'secret_key': self.secret_key,
            'created_at': datetime.utcnow().isoformat(),
            'algorithm': 'HS256'
        }
        
        self.storage.save_json('jwt_secret.json', secret_data)
        print(f"✅ Generated and saved new JWT secret")
        print(f"💡 To use this secret on other hosts, set: JWT_SECRET_KEY={self.secret_key}")
    
    def create_token(
        self,
        user_id: str,
        username: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
        expires_days: int = 7
    ) -> Optional[str]:
        """
        Create a JWT token for a user.
        
        IMPORTANT: This should ONLY be called on the auth server!
        API execution providers should NEVER generate tokens.
        
        Args:
            user_id: Unique user identifier
            username: Username
            role: User role (default: "user")
            metadata: Optional additional claims
            expires_days: Token expiration in days
            
        Returns:
            JWT token string or None if not auth server
        """
        if not self.is_auth_server:
            print("❌ ERROR: Attempted to create token on API execution provider!")
            print("   Tokens can ONLY be created on the auth server")
            print(f"   Set IS_AUTH_SERVER=true on {os.getenv('AUTH_SERVER_DOMAIN')}")
            return None
            
        if not self.secret_key:
            print("❌ ERROR: No JWT secret key available!")
            print("   Cannot create token without secret key")
            print("   Check S3 storage or set JWT_SECRET_KEY environment variable")
            return None
        
        # Create JWT claims
        now = datetime.utcnow()
        claims = {
            "sub": user_id,  # Subject (user ID)
            "iat": now,  # Issued at
            "exp": now + timedelta(days=expires_days),  # Expiration
            "nbf": now,  # Not before
            "iss": "api.oneaurica.com",  # Issuer
            "aud": "aurica-apps",  # Audience
            "username": username,
            "role": role
        }
        
        # Add metadata if provided
        if metadata:
            claims["metadata"] = metadata
        
        # Create and sign the token
        try:
            token = jwt.encode(
                claims,
                self.secret_key,
                algorithm="HS256"
            )
            print(f"✅ Created JWT token for user: {username}")
            return token
        except Exception as e:
            print(f"❌ ERROR: Failed to create JWT token: {e}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token claims or None if invalid
        """
        if not self.secret_key:
            print("⚠️  No JWT secret key available for token verification")
            if not self.is_auth_server:
                print("   Attempting to fetch secret from auth server...")
                self._fetch_secret_from_auth_server()
                if not self.secret_key:
                    print("❌ Still no secret key available - cannot verify token")
                    return None
            else:
                print("❌ Auth server has no secret key - check configuration")
                return None
        
        try:
            # Decode and verify the token
            claims = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"],
                audience="aurica-apps",
                issuer="api.oneaurica.com"
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            print("⚠️  Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"⚠️  Invalid token: {e}")
            return None
    
    def get_secret_info(self) -> Dict[str, Any]:
        """
        Get information about the JWT secret (for distribution to other hosts).
        
        Returns:
            Secret information
        """
        return {
            "algorithm": "HS256",
            "issuer": "api.oneaurica.com",
            "audience": "aurica-apps",
            "secret_key": self.secret_key,
            "expires_days": 7
        }
    
    def get_jwks(self) -> Dict[str, Any]:
        """
        Get JSON Web Key Set (JWKS) for token verification.
        
        For HMAC (HS256), this returns the symmetric key.
        Note: In production, consider switching to RSA for better security.
        
        Returns:
            JWKS dictionary
        """
        # For HMAC, the secret_key is already base64url-encoded (from secrets.token_urlsafe)
        # Don't double-encode it!
        return {
            "keys": [
                {
                    "kty": "oct",  # Octet sequence (symmetric key)
                    "use": "sig",
                    "alg": "HS256",
                    "k": self.secret_key  # Already base64url-encoded
                }
            ]
        }
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh an existing token (if valid and not expired).
        
        Args:
            token: Existing JWT token
        
        Returns:
            New JWT token or None if invalid
        """
        claims = self.verify_token(token)
        
        if not claims:
            return None
        
        # Create a new token with the same claims but new expiration
        return self.create_token(
            user_id=claims["sub"],
            username=claims["username"],
            role=claims.get("role", "user"),
            metadata=claims.get("metadata")
        )


# Global JWT manager instance
jwt_manager = JWTManager()
