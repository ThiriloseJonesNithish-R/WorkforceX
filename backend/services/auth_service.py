import datetime
import jwt
import hashlib
from backend.config import Config

try:
    import bcrypt
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(hashed_password: str, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return check_password_sha256(hashed_password, password)
except ImportError:
    print("Warning: bcrypt not found. Using SHA-256 for auth service hashing.")
    def hash_password(password: str) -> str:
        salt = "workforcex_salt"
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

    def check_password(hashed_password: str, password: str) -> bool:
        salt = "workforcex_salt"
        computed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        return computed == hashed_password

def check_password_sha256(hashed_password: str, password: str) -> bool:
    salt = "workforcex_salt"
    computed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return computed == hashed_password

def generate_token(username: str, role: str) -> str:
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}
