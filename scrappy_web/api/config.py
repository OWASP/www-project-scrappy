import os
from typing import Optional

class Settings:
    """
    Configuration loaded from environment variables.
    All sensitive values MUST be set via environment in production.
    """
    
    # Security
    SECRET_KEY: str = os.getenv("SCRAPPY_SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("SCRAPPY_TOKEN_EXPIRE_MINUTES", "30"))
    
    # File Upload Limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("SCRAPPY_MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_CONTENT_TYPES: list = ["application/pdf"]
    
    # Rate Limiting
    LOGIN_RATE_LIMIT: str = os.getenv("SCRAPPY_LOGIN_RATE_LIMIT", "5/minute")
    JOB_RATE_LIMIT: str = os.getenv("SCRAPPY_JOB_RATE_LIMIT", "10/minute")
    
    # Paths
    UPLOAD_DIR: str = os.getenv("SCRAPPY_UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "../../temp_uploads"))
    
    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration. Raises ValueError if invalid."""
        if not cls.SECRET_KEY:
            raise ValueError(
                "SCRAPPY_SECRET_KEY environment variable is required. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SCRAPPY_SECRET_KEY must be at least 32 characters")

settings = Settings()
