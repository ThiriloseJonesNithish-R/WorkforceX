from flask import request, jsonify
from functools import wraps
from backend.services.auth_service import decode_token
from backend.database.mongo import Database

def token_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = ["professional", "organization"]
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
        
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if "Authorization" in request.headers:
                token = request.headers["Authorization"]
                
            if not token:
                return jsonify({"error": "Authorization token is missing."}), 401
                
            payload = decode_token(token)
            if "error" in payload:
                return jsonify({"error": payload["error"]}), 401
                
            role = payload.get("role")
            if role not in allowed_roles:
                return jsonify({"error": "Access denied. Insufficient permissions."}), 403
                
            username = payload.get("username")
            db = Database.get_db()
            
            user = None
            if role == "professional":
                user = db["professionals"].find_one({"username": username})
            elif role == "organization":
                user = db["organizations"].find_one({"username": username})
                
            if not user:
                return jsonify({"error": "Authenticated user not found in database."}), 401
                
            # Attach user and role to request context
            request.current_user = user
            request.user_role = role
            
            return f(*args, **kwargs)
        return decorated
    return decorator
