"""
JWT Authentication component for zen projects.

This component provides comprehensive JWT authentication functionality including:
- Token generation and validation
- Middleware for popular web frameworks (Flask, FastAPI)
- Role-based access control
- Token refresh functionality

Usage:
    from auth.jwt_handler import JWTHandler, create_user_tokens
    from auth.middleware import FlaskJWTMiddleware, require_auth
    
    # Create JWT handler
    jwt_handler = JWTHandler("your-secret-key")
    
    # Generate tokens for a user
    tokens = create_user_tokens("user123", "user@example.com", ["user"], jwt_handler)
    
    # Use with Flask
    from flask import Flask
    app = Flask(__name__)
    FlaskJWTMiddleware(app, jwt_handler, excluded_paths=['/login', '/register'])
    
    @app.route('/protected')
    @require_auth(roles=['user'])
    def protected_route():
        return {"message": "Access granted"}
"""

from .jwt_handler import (
    JWTHandler,
    create_user_tokens,
    generate_rsa_keys
)

from .middleware import (
    JWTMiddleware,
    jwt_required,
    extract_user_info,
    check_user_permission
)

# Conditional imports based on available frameworks
try:
    from .middleware import FlaskJWTMiddleware, require_auth
    __all_flask__ = ['FlaskJWTMiddleware', 'require_auth']
except ImportError:
    __all_flask__ = []

try:
    from .middleware import FastAPIJWTBearer, create_fastapi_auth_dependency, require_roles
    __all_fastapi__ = ['FastAPIJWTBearer', 'create_fastapi_auth_dependency', 'require_roles']
except ImportError:
    __all_fastapi__ = []

__all__ = [
    # Core JWT functionality
    'JWTHandler',
    'create_user_tokens', 
    'generate_rsa_keys',
    
    # Middleware
    'JWTMiddleware',
    'jwt_required',
    'extract_user_info',
    'check_user_permission',
] + __all_flask__ + __all_fastapi__

__version__ = "2.0.0"
__author__ = "zen"