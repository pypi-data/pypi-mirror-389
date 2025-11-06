"""
JWT authentication middleware for web frameworks.

Provides middleware classes and decorators for:
- Flask applications
- FastAPI applications  
- Generic WSGI applications
- Function decorators for route protection
"""

import functools
from typing import Callable, Optional, List, Dict, Any
import jwt

try:
    from flask import request, jsonify, g
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

try:
    from fastapi import HTTPException, status, Depends
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

class JWTMiddleware:
    """Base JWT middleware class."""
    
    def __init__(self, jwt_handler, excluded_paths: List[str] = None):
        """
        Initialize JWT middleware.
        
        Args:
            jwt_handler: JWTHandler instance
            excluded_paths: Paths to exclude from authentication
        """
        self.jwt_handler = jwt_handler
        self.excluded_paths = excluded_paths or []
    
    def extract_token_from_header(self, auth_header: str) -> Optional[str]:
        """
        Extract token from Authorization header.
        
        Args:
            auth_header: Authorization header value
            
        Returns:
            JWT token or None
        """
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]

# Flask Middleware
if HAS_FLASK:
    class FlaskJWTMiddleware(JWTMiddleware):
        """Flask JWT middleware."""
        
        def __init__(self, app, jwt_handler, excluded_paths: List[str] = None):
            super().__init__(jwt_handler, excluded_paths)
            self.app = app
            self.init_app()
        
        def init_app(self):
            """Initialize Flask app with JWT middleware."""
            self.app.before_request(self.before_request)
        
        def before_request(self):
            """Flask before_request handler."""
            # Skip excluded paths
            if request.path in self.excluded_paths:
                return
            
            # Extract token
            auth_header = request.headers.get('Authorization')
            token = self.extract_token_from_header(auth_header)
            
            if not token:
                return jsonify({'error': 'Missing authorization token'}), 401
            
            try:
                # Verify token
                payload = self.jwt_handler.verify_token(token)
                g.current_user = payload
                g.user_id = payload.get('user_id')
                g.user_email = payload.get('email')
                g.user_roles = payload.get('roles', [])
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
    
    def require_auth(roles: List[str] = None):
        """
        Flask decorator to require authentication and optionally specific roles.
        
        Args:
            roles: Required roles for access
        """
        def decorator(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user'):
                    return jsonify({'error': 'Authentication required'}), 401
                
                if roles:
                    user_roles = g.get('user_roles', [])
                    if not any(role in user_roles for role in roles):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# FastAPI Middleware  
if HAS_FASTAPI:
    class FastAPIJWTBearer(HTTPBearer):
        """FastAPI JWT Bearer authentication."""
        
        def __init__(self, jwt_handler, auto_error: bool = True):
            super().__init__(auto_error=auto_error)
            self.jwt_handler = jwt_handler
        
        async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
            """Verify JWT token."""
            if credentials:
                try:
                    payload = self.jwt_handler.verify_token(credentials.credentials)
                    return payload
                except jwt.ExpiredSignatureError:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired"
                    )
                except jwt.InvalidTokenError:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization credentials"
                )
    
    def create_fastapi_auth_dependency(jwt_handler):
        """
        Create FastAPI dependency for JWT authentication.
        
        Args:
            jwt_handler: JWTHandler instance
            
        Returns:
            FastAPI dependency function
        """
        security = FastAPIJWTBearer(jwt_handler)
        
        async def get_current_user(payload: dict = Depends(security)):
            return {
                'user_id': payload.get('user_id'),
                'email': payload.get('email'),
                'roles': payload.get('roles', [])
            }
        
        return get_current_user
    
    def require_roles(required_roles: List[str]):
        """
        FastAPI dependency to require specific roles.
        
        Args:
            required_roles: List of required roles
        """
        def role_checker(current_user: dict = Depends(create_fastapi_auth_dependency)):
            user_roles = current_user.get('roles', [])
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        
        return role_checker

# Generic decorators
def jwt_required(jwt_handler, roles: List[str] = None):
    """
    Generic JWT authentication decorator.
    
    Args:
        jwt_handler: JWTHandler instance
        roles: Required roles for access
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # This is a generic implementation
            # In practice, you'd adapt this to your specific framework
            
            # For demonstration, assume token is passed as first argument
            if args and isinstance(args[0], str):
                token = args[0]
                try:
                    payload = jwt_handler.verify_token(token)
                    
                    if roles:
                        user_roles = payload.get('roles', [])
                        if not any(role in user_roles for role in roles):
                            raise PermissionError("Insufficient permissions")
                    
                    # Pass payload as additional argument
                    return f(payload, *args[1:], **kwargs)
                    
                except jwt.ExpiredSignatureError:
                    raise ValueError("Token has expired")
                except jwt.InvalidTokenError:
                    raise ValueError("Invalid token")
            else:
                raise ValueError("Token required")
        
        return decorated_function
    return decorator

# Utility functions
def extract_user_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from JWT payload.
    
    Args:
        payload: JWT token payload
        
    Returns:
        User information dictionary
    """
    return {
        'user_id': payload.get('user_id'),
        'email': payload.get('email'),
        'roles': payload.get('roles', []),
        'exp': payload.get('exp'),
        'iat': payload.get('iat')
    }

def check_user_permission(user_roles: List[str], required_roles: List[str]) -> bool:
    """
    Check if user has required permissions.
    
    Args:
        user_roles: User's roles
        required_roles: Required roles
        
    Returns:
        True if user has permission
    """
    return any(role in user_roles for role in required_roles)

if __name__ == "__main__":
    # Example usage
    from jwt_handler import JWTHandler
    
    # Create JWT handler
    handler = JWTHandler("your-secret-key")
    
    # Example with generic decorator
    @jwt_required(handler, roles=['admin'])
    def protected_function(user_payload, data):
        print(f"Protected function called by user: {user_payload['email']}")
        return f"Hello {user_payload['email']}, data: {data}"
    
    # Create a test token
    from jwt_handler import create_user_tokens
    tokens = create_user_tokens("123", "admin@example.com", ["admin"], handler)
    
    # Test the protected function
    try:
        result = protected_function(tokens['access_token'], "test data")
        print(result)
    except Exception as e:
        print(f"Error: {e}")