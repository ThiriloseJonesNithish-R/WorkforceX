import os

class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://sowndi_gowri:sowndi_gowri@unicorn.vduucnx.mongodb.net/?appName=Unicorn")
    DB_NAME = "WorkForceX"
    JWT_SECRET = os.environ.get("JWT_SECRET", "workforcex_secret_jwt_key_2026_@!")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads")))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
