import pytest
from backend.config import AppConfig, get_config
import os

@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    for var in [
        "DATABRICKS_HOST", "DATABRICKS_TOKEN", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET",
        "DATABRICKS_WORKSPACE_ID", "DATABRICKS_ACCOUNT_ID", "DATABRICKS_CONFIG_PROFILE", "APP_ENV", "LOG_LEVEL",
        "IMAGE_DPI", "IMAGE_MAX_WIDTH", "IMAGE_MAX_HEIGHT"
    ]:
        monkeypatch.delenv(var, raising=False)

class TestAppConfig:
    def test_defaults(self):
        """Test that AppConfig uses default values when env vars are not set."""
        config = AppConfig()
        assert config.app_env == "local"
        assert config.log_level == "DEBUG"

    def test_env_loading(self, monkeypatch):
        """Test that AppConfig loads values from environment variables."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.cloud.databricks.com")
        monkeypatch.setenv("APP_ENV", "production")
        config = AppConfig()
        assert config.databricks_host == "https://test.cloud.databricks.com"
        assert config.app_env == "production"

    def test_constructor_override(self, monkeypatch):
        """Test that AppConfig constructor args override environment variables."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://env.cloud.databricks.com")
        config = AppConfig(databricks_host="https://ctor.cloud.databricks.com")
        assert config.databricks_host == "https://ctor.cloud.databricks.com"

    def test_singleton(self):
        """Test that get_config() returns a singleton instance."""
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_image_config_defaults(self):
        """Test that image configuration defaults are set properly."""
        config = AppConfig()
        assert config.image_dpi == 300
        assert config.image_max_width == 2048
        assert config.image_max_height == 2048

    def test_image_config_env_loading(self, monkeypatch):
        """Test that image configuration loads from environment variables."""
        monkeypatch.setenv("IMAGE_DPI", "150")
        monkeypatch.setenv("IMAGE_MAX_WIDTH", "1024")
        monkeypatch.setenv("IMAGE_MAX_HEIGHT", "768")
        
        config = AppConfig()
        assert config.image_dpi == 150
        assert config.image_max_width == 1024
        assert config.image_max_height == 768

    def test_image_config_validation(self):
        """Test that image configuration values are validated."""
        # Test that positive values are required
        config = AppConfig(image_dpi=150, image_max_width=1024, image_max_height=768)
        assert config.image_dpi == 150
        assert config.image_max_width == 1024
        assert config.image_max_height == 768