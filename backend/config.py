import os

def load_env():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        env_path = os.path.join(current_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        key = k.strip()
                        if key not in os.environ:
                            os.environ[key] = v.strip()
            break
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent

load_env()

class Config:
    MONGO_URI = os.environ.get("MONGO_URI") or "mongodb://127.0.0.1:27017"
    DB_NAME = "WorkForceX"
    JWT_SECRET = os.environ.get("JWT_SECRET") or "workforcex_secret_dev_key_2026"
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads")))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
