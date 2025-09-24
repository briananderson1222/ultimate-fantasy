"""
Configuration settings for Ultimate Fantasy Platform API
"""

import os


class Settings:
    """Application settings and configuration"""

    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://ultimate_fantasy:password@localhost:5432/ultimate_fantasy",
    )

    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database pool settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    DB_POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    DB_ISOLATION_LEVEL: str = os.getenv("DB_ISOLATION_LEVEL", "READ_COMMITTED")
    DB_HEALTH_CHECK_INTERVAL: int = int(os.getenv("DB_HEALTH_CHECK_INTERVAL", "30"))
    DB_MAX_RETRIES: int = int(os.getenv("DB_MAX_RETRIES", "3"))
    DB_RETRY_DELAY: float = float(os.getenv("DB_RETRY_DELAY", "1.0"))

    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # API settings
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    API_PREFIX: str = f"/api/{API_VERSION}"

    # CORS settings
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:3001"
    ).split(",")

    # Sports data API settings
    ESPN_API_KEY: str | None = os.getenv("ESPN_API_KEY")
    THE_ATHLETIC_API_KEY: str | None = os.getenv("THE_ATHLETIC_API_KEY")

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")


# Global settings instance
settings = Settings()
