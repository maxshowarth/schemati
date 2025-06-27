"""
Tests for the frontend application.
"""

import pytest
import sys
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.append(str(Path(__file__).parent.parent))

def test_frontend_imports():
    """Test that the frontend module can be imported."""
    import frontend
    import frontend.app
    
    # Check that main function exists
    assert hasattr(frontend.app, 'main')
    assert callable(frontend.app.main)
    
    # Check that upload_files function exists
    assert hasattr(frontend.app, 'upload_files')
    assert callable(frontend.app.upload_files)
    
    # Check that show_volume_contents function exists
    assert hasattr(frontend.app, 'show_volume_contents')
    assert callable(frontend.app.show_volume_contents)

def test_frontend_module_structure():
    """Test that the frontend package structure is correct."""
    import frontend
    
    # Check that the package has a docstring
    assert frontend.__doc__ is not None
    assert "Streamlit" in frontend.__doc__