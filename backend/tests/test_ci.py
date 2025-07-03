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
        import backend.databricks.auth
        import backend.logging
        import backend.llm
        import backend.llm.openai_client
        import backend.llm.document_parser
        import backend.llm.prompt_loader
        assert True
    except ImportError as e:
        assert False, f"Failed to import backend modules: {e}"


def test_main_module():
    """Test the main module."""
    import main
    # Test that main function exists and is callable
    assert hasattr(main, 'main')
    assert callable(main.main)