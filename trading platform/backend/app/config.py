"""Configuration management using pydantic-settings"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    database_url: str = "postgresql://trading_user:trading_pass@localhost:5432/trading_analytics"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_log_level: str = "info"
    
    # Data Provider API Keys
    polygon_api_key: Optional[str] = None
    ibkr_api_key: Optional[str] = None
    
    # Alert Notification Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Application Configuration
    log_level: str = "INFO"
    environment: str = "development"
    
    def validate_required_settings(self) -> None:
        """Validate that required settings are present"""
        errors = []
        
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Global settings instance
settings = Settings()
