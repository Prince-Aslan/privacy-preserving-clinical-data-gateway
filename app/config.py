import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Privacy-Preserving Clinical Data Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Secret keys for JWT & Cryptography
    SECRET_KEY: str = os.getenv("SECRET_KEY", "clinical_privacy_secret_key_2026_miva_mit_super_secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # AES-256 Secret Key (32 bytes = 256 bits)
    AES_SECRET_KEY: str = os.getenv("AES_SECRET_KEY", "gK3sP9vL1mN5qR8tW2xY4zA7bC0dE6fH")
    
    # ClickHouse Database Connection
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    CLICKHOUSE_DB: str = os.getenv("CLICKHOUSE_DB", "clinical_gateway")
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "")

    class Config:
        case_sensitive = True

settings = Settings()
