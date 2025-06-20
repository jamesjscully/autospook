"""
AutoSpook Authentication Middleware
Handles token-based authentication for API access
"""

import os
import hashlib
import hmac
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class TokenAuth:
    """Token-based authentication system"""
    
    def __init__(self, token_file="tokens.txt"):
        self.token_file = token_file
        self.tokens_cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5 minutes cache TTL
    
    def _load_tokens(self):
        """Load tokens from file with caching"""
        try:
            if not os.path.exists(self.token_file):
                logger.warning(f"Token file {self.token_file} not found")
                return {}
            
            # Check if cache is still valid
            file_mtime = os.path.getmtime(self.token_file)
            current_time = datetime.now().timestamp()
            
            if (file_mtime <= self.cache_timestamp and 
                current_time - self.cache_timestamp < self.cache_ttl):
                return self.tokens_cache
            
            # Reload tokens from file
            tokens = {}
            with open(self.token_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('|')
                    if len(parts) >= 5:
                        token, name, created, expires, status = parts[:5]
                        
                        # Parse expiry date
                        try:
                            expire_dt = datetime.strptime(expires, "%Y-%m-%d %H:%M:%S UTC")
                            expire_dt = expire_dt.replace(tzinfo=timezone.utc)
                        except ValueError:
                            logger.warning(f"Invalid date format for token {name}")
                            continue
                        
                        tokens[token] = {
                            'name': name,
                            'created': created,
                            'expires': expire_dt,
                            'status': status
                        }
            
            # Update cache
            self.tokens_cache = tokens
            self.cache_timestamp = current_time
            return tokens
            
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            return {}
    
    def validate_token(self, token):
        """Validate if token is active and not expired"""
        if not token:
            return False, "No token provided"
        
        tokens = self._load_tokens()
        
        if token not in tokens:
            logger.warning(f"Invalid token attempted: {token[:12]}...")
            return False, "Invalid token"
        
        token_data = tokens[token]
        
        # Check if token is active
        if token_data['status'] != 'active':
            logger.warning(f"Revoked token attempted: {token_data['name']}")
            return False, "Token revoked"
        
        # Check if token is expired
        now = datetime.now(timezone.utc)
        if now > token_data['expires']:
            logger.warning(f"Expired token attempted: {token_data['name']}")
            return False, "Token expired"
        
        logger.info(f"Valid token used: {token_data['name']}")
        return True, token_data['name']
    
    def get_token_info(self, token):
        """Get information about a token"""
        tokens = self._load_tokens()
        return tokens.get(token)


# Global auth instance
auth = TokenAuth()


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth in development if explicitly disabled
        if (current_app.config.get('DEBUG') and 
            os.getenv('SKIP_AUTH_IN_DEV', 'False').lower() == 'true'):
            logger.warning("⚠️  AUTH SKIPPED IN DEVELOPMENT MODE")
            return f(*args, **kwargs)
        
        # Get token from various sources
        token = None
        
        # 1. Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # 2. Check form data (for web form submissions)
        elif request.form and 'auth_token' in request.form:
            token = request.form.get('auth_token')
        
        # 3. Check JSON body
        elif request.is_json and request.json and 'auth_token' in request.json:
            token = request.json.get('auth_token')
        
        # 4. Check query parameter (least secure, for testing only)
        elif request.args.get('token'):
            token = request.args.get('token')
            logger.warning("Token passed as query parameter - not recommended for production")
        
        if not token:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please provide a valid auth token'
            }), 401
        
        # Validate token
        is_valid, message = auth.validate_token(token)
        
        if not is_valid:
            logger.warning(f"Authentication failed from {request.remote_addr}: {message}")
            return jsonify({
                'error': 'Authentication failed',
                'message': message
            }), 401
        
        # Store token info in request context for use in route
        request.auth_user = message  # User name from token
        request.auth_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_auth_status():
    """Get current authentication status"""
    if hasattr(request, 'auth_user'):
        return {
            'authenticated': True,
            'user': request.auth_user,
            'token_preview': request.auth_token[:12] + '...' if len(request.auth_token) > 12 else request.auth_token
        }
    else:
        return {
            'authenticated': False,
            'user': None,
            'token_preview': None
        }


def init_auth_routes(app):
    """Initialize authentication-related routes"""
    
    @app.route('/auth/status')
    @require_auth
    def auth_status():
        """Check authentication status"""
        return jsonify(get_auth_status())
    
    @app.route('/auth/validate', methods=['POST'])
    def validate_token_route():
        """Validate a token without requiring authentication"""
        token = request.json.get('token') if request.is_json else request.form.get('token')
        
        if not token:
            return jsonify({'valid': False, 'message': 'No token provided'}), 400
        
        is_valid, message = auth.validate_token(token)
        
        return jsonify({
            'valid': is_valid,
            'message': message,
            'token_preview': token[:12] + '...' if len(token) > 12 else token
        })


# Rate limiting for auth endpoints
def setup_auth_rate_limiting(app):
    """Setup rate limiting for authentication endpoints"""
    # This would integrate with Flask-Limiter if installed
    # For now, we'll use the existing rate_limiter
    pass