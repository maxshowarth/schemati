"""Simple test to verify CI workflow functionality."""

def test_basic_functionality():
    """Test that basic Python functionality works."""
    assert 1 + 1 == 2
    assert "hello" == "hello"


def test_imports():
    """Test that we can import our modules."""
    try:
        import backend
        import backend.config
        import backend.auth
        import backend.logging
        assert True
    except ImportError as e:
        assert False, f"Failed to import backend modules: {e}"


def test_main_module():
    """Test the main module."""
    import main
    # Test that main function exists and is callable
    assert hasattr(main, 'main')
    assert callable(main.main)