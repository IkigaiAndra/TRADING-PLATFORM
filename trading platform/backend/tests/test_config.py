"""Tests for configuration management"""

import pytest
from app.config import Settings


def test_settings_default_values():
    """Test that settings have sensible default values"""
    settings = Settings()
    
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.log_level == "INFO"
    assert settings.environment == "development"
    assert settings.database_pool_size == 20
    assert settings.database_max_overflow == 10


def test_settings_validation_passes_with_database_url():
    """Test that validation passes when database_url is set"""
    settings = Settings(database_url="postgresql://user:pass@localhost/db")
    
    # Should not raise
    settings.validate_required_settings()


def test_settings_validation_fails_without_database_url():
    """Test that validation fails when database_url is missing"""
    settings = Settings(database_url="")
    
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        settings.validate_required_settings()


def test_settings_from_env_file(monkeypatch):
    """Test that settings can be loaded from environment variables"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    settings = Settings()
    
    assert settings.database_url == "postgresql://test:test@localhost/test"
    assert settings.api_port == 9000
    assert settings.log_level == "DEBUG"
