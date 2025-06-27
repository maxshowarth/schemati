import pytest
from backend.config import AppConfig, get_config
import os

@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    for var in [
        "DATABRICKS_HOST", "DATABRICKS_TOKEN", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET",
        "DATABRICKS_WORKSPACE_ID", "DATABRICKS_ACCOUNT_ID", "DATABRICKS_CONFIG_PROFILE", "APP_ENV", "LOG_LEVEL"
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