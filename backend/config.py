# Inspired by https://github.com/databricks-solutions/brickhouse-brands-demo/blob/main/backend/app/auth.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    """Application configuration using Pydantic BaseSettings.

    Loads configuration from environment variables and .env file (if present).
    Fields are type-checked and validated. Defaults are provided where appropriate.
    """
    # Databricks
    databricks_host: Optional[str] = None
    databricks_token: Optional[str] = None
    databricks_client_id: Optional[str] = None
    databricks_client_secret: Optional[str] = None
    databricks_workspace_id: Optional[str] = None
    databricks_account_id: Optional[str] = None
    databricks_config_profile: Optional[str] = None
    databricks_catalog: Optional[str] = None
    databricks_schema: Optional[str] = None
    databricks_volume: Optional[str] = None

    # Application
    app_env: str = "local"
    log_level: str = "DEBUG"
    allowed_image_extensions: list[str] = [".jpg", ".jpeg", ".png"]
    allowed_pdf_extensions: list[str] = [".pdf"]
    
    # Image processing
    image_dpi: int = 300
    image_max_width: int = 2048
    image_max_height: int = 2048

    # Fragment configuration
    fragment_tile_width: int = 1024
    fragment_tile_height: int = 1024
    fragment_overlap_ratio: float = 0.1
    fragment_complexity_threshold: float = 0.03
    fragment_dynamic_enabled: bool = False


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

_config: Optional[AppConfig] = None

def get_config() -> AppConfig:
    """Return the AppConfig instance (singleton pattern)."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config

def set_config_for_test(**kwargs):
    """For testing only: override the AppConfig instance with new values."""
    global _config
    _config = AppConfig(**kwargs)
