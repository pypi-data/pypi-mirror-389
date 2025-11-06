"""
JWT authentication handler for zen projects.

Provides comprehensive JWT token management including:
- Token generation with custom claims
- Token validation and decoding
- Token refresh functionality
- Configurable expiration times
"""

import jwt
import datetime
from typing import Dict, Any, Optional, Union
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class JWTHandler:
    """
    JWT token handler with support for both symmetric and asymmetric signing.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", 
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7):
        """
        Initialize JWT handler.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (HS256, RS256, etc.)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(self, data: Dict[str, Any], 
                          expires_delta: Optional[datetime.timedelta] = None) -> str:
        """
        Create an access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any],
                           expires_delta: Optional[datetime.timedelta] = None) -> str:
        """
        Create a refresh token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Custom expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(
                days=self.refresh_token_expire_days
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
            ValueError: Token type mismatch
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                raise ValueError(f"Expected {token_type} token, got {payload.get('type')}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create a new access token from a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            jwt.ExpiredSignatureError: Refresh token has expired
            jwt.InvalidTokenError: Refresh token is invalid
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, token_type="refresh")
        
        # Create new access token with same user data
        user_data = {k: v for k, v in payload.items() 
                    if k not in ["exp", "iat", "type"]}
        
        return self.create_access_token(user_data)
    
    def get_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token payload without verification (for debugging).
        
        Args:
            token: JWT token
            
        Returns:
            Token payload or None if invalid
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except:
            return None

# Utility functions for common use cases
def create_user_tokens(user_id: str, email: str, roles: list = None, 
                      jwt_handler: JWTHandler = None) -> Dict[str, str]:
    """
    Create access and refresh tokens for a user.
    
    Args:
        user_id: User identifier
        email: User email
        roles: User roles/permissions
        jwt_handler: JWT handler instance
        
    Returns:
        Dictionary with access_token and refresh_token
    """
    if jwt_handler is None:
        raise ValueError("JWT handler is required")
    
    user_data = {
        "user_id": user_id,
        "email": email,
        "roles": roles or []
    }
    
    access_token = jwt_handler.create_access_token(user_data)
    refresh_token = jwt_handler.create_refresh_token({"user_id": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

def generate_rsa_keys() -> tuple:
    """
    Generate RSA key pair for RS256 algorithm.
    
    Returns:
        Tuple of (private_key_pem, public_key_pem)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode(), public_pem.decode()

if __name__ == "__main__":
    # Example usage
    handler = JWTHandler("your-secret-key-here")
    
    # Create tokens for a user
    tokens = create_user_tokens(
        user_id="123",
        email="user@example.com", 
        roles=["user", "admin"],
        jwt_handler=handler
    )
    
    print("Generated tokens:")
    print(f"Access Token: {tokens['access_token'][:50]}...")
    print(f"Refresh Token: {tokens['refresh_token'][:50]}...")
    
    # Verify access token
    try:
        payload = handler.verify_token(tokens['access_token'])
        print(f"Token valid for user: {payload['email']}")
    except Exception as e:
        print(f"Token verification failed: {e}")