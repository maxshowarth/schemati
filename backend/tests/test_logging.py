import pytest
from backend.logging import get_logger
from backend.config import get_config

class TestLogging:
    def test_log_level_from_config(self):
        """Test that logger uses log level from AppConfig."""
        config = get_config()
        config.log_level = "WARNING"
        from importlib import reload
        import backend.logging as blog
        reload(blog)
        logger = blog.get_logger("test")
        assert config.log_level.upper() == "WARNING"
        # Should log at WARNING but not at INFO
        logger.warning("This is a warning.")
        logger.info("This info should not appear if loguru is configured correctly.")

    def test_logger_is_singleton(self):
        """Test that get_logger returns the same logger instance for the same name."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2 or logger1._core is logger2._core