"""
Configuration settings for the Ailoos Coordinator Service.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="ailoos_coordinator", env="DB_NAME")
    user: str = Field(default="ailoos_coordinator", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD", description="Database password - must be set in production")
    pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")  # 1 hour
    echo: bool = Field(default=False, env="DB_ECHO")

    # Cloud SQL specific settings
    cloud_sql_instance: Optional[str] = Field(default=None, env="CLOUD_SQL_INSTANCE")
    use_iam_auth: bool = Field(default=False, env="DB_USE_IAM_AUTH")
    ssl_mode: str = Field(default="require", env="DB_SSL_MODE")

    # Connection retry settings
    max_retries: int = Field(default=3, env="DB_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="DB_RETRY_DELAY")

    # Read replica settings
    read_replica_host: Optional[str] = Field(default=None, env="DB_READ_REPLICA_HOST")
    use_read_replica: bool = Field(default=False, env="DB_USE_READ_REPLICA")

    @property
    def url(self) -> str:
        """Database connection URL with Cloud SQL support."""
        if self.cloud_sql_instance:
            # Cloud SQL connection string
            return f"postgresql://{self.user}:{self.password}@/{self.name}?host=/cloudsql/{self.cloud_sql_instance}&sslmode={self.ssl_mode}"
        else:
            # Standard PostgreSQL connection
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"

    @property
    def read_replica_url(self) -> Optional[str]:
        """Read replica connection URL."""
        if not self.use_read_replica or not self.read_replica_host:
            return None
        return f"postgresql://{self.user}:{self.password}@{self.read_replica_host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD", description="Redis password - optional for local development")
    key_prefix: str = Field(default="ailoos:", env="REDIS_KEY_PREFIX")

    @property
    def url(self) -> str:
        """Redis connection URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class AuthSettings(BaseSettings):
    """Authentication and authorization settings."""
    jwt_secret_key: str = Field(default="change-this-in-production-to-a-secure-random-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    node_token_expiration_days: int = Field(default=30, env="NODE_TOKEN_EXPIRATION_DAYS")


class APISettings(BaseSettings):
    """API configuration settings."""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")


class CoordinatorSettings(BaseSettings):
    """Coordinator service settings."""
    session_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    max_concurrent_sessions: int = Field(default=100, env="MAX_CONCURRENT_SESSIONS")
    min_nodes_per_session: int = Field(default=3, env="MIN_NODES_PER_SESSION")
    max_nodes_per_session: int = Field(default=50, env="MAX_NODES_PER_SESSION")
    heartbeat_interval_seconds: int = Field(default=30, env="HEARTBEAT_INTERVAL_SECONDS")
    node_timeout_seconds: int = Field(default=300, env="NODE_TIMEOUT_SECONDS")


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Database
    database: DatabaseSettings = DatabaseSettings()

    # Redis
    redis: RedisSettings = RedisSettings()

    # Authentication
    auth: AuthSettings = AuthSettings()

    # API
    api: APISettings = APISettings()

    # Coordinator
    coordinator: CoordinatorSettings = CoordinatorSettings()

    # External services
    rewards_service_url: str = Field(default="http://localhost:8001", env="REWARDS_SERVICE_URL", description="URL for the rewards service")
    verification_service_url: str = Field(default="http://localhost:8002", env="VERIFICATION_SERVICE_URL", description="URL for the verification service")
    auditing_service_url: str = Field(default="http://localhost:8003", env="AUDITING_SERVICE_URL", description="URL for the auditing service")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()