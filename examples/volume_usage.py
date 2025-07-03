"""
Example demonstrating the Volume and VolumeFileStore classes.

This shows how to use the refactored classes for better
object-oriented design and explicit dependency injection.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.routers.volume import Volume, VolumeFileStore, create_volume_from_config, create_volume_file_store_from_config
from backend.auth import get_databricks_auth
from unittest.mock import MagicMock


def example_using_classes():
    """Example using the Volume and VolumeFileStore classes directly."""
    
    # Create a Volume instance - pure data model
    volume = Volume(
        catalog="my_catalog",
        schema_name="my_schema", 
        volume_name="my_volume"
    )
    
    print(f"Volume full name: {volume.get_full_name()}")
    print(f"Volume path: {volume.get_volume_path()}")
    print(f"File path for 'data.csv': {volume.get_file_path('data.csv')}")
    
    # Create a VolumeFileStore with explicit dependencies
    # In real usage, you would use: client = get_databricks_auth().get_workspace_client()
    mock_client = MagicMock()  # Using mock for demonstration
    file_store = VolumeFileStore(volume, mock_client)
    
    # Use the file store for operations
    print(f"Volume exists: {file_store.volume_exists()}")
    print(f"Files in volume: {file_store.list_files()}")
    

def example_using_helper_functions():
    """Example using helper functions for config-based creation."""
    
    # Set up test config first
    from backend.config import set_config_for_test
    set_config_for_test(
        databricks_catalog="config_catalog",
        databricks_schema="config_schema",
        databricks_volume="config_volume"
    )
    
    # Create Volume from config (with optional overrides)
    volume = create_volume_from_config(
        catalog="override_catalog"  # Override catalog, use config for schema/volume
    )
    
    # Create VolumeFileStore from config (with explicit mock client)
    mock_client = MagicMock()
    file_store = create_volume_file_store_from_config(
        catalog="my_catalog",
        schema="my_schema", 
        volume_name="my_volume",
        client=mock_client
    )
    
    print(f"Config-based volume: {file_store.volume.get_full_name()}")


def example_download_file_as_bytes():
    """Example showing the download_file_as_bytes method."""
    
    volume = Volume(catalog="catalog", schema_name="schema", volume_name="volume")
    mock_client = MagicMock()
    
    # Mock the download response
    mock_response = MagicMock()
    mock_response.contents.read.return_value = b"file content as bytes"
    mock_client.files.download.return_value = mock_response
    
    file_store = VolumeFileStore(volume, mock_client)
    
    # Download file as bytes - useful for document loaders
    file_bytes = file_store.download_file_as_bytes("document.pdf")
    print(f"Downloaded {len(file_bytes)} bytes")



if __name__ == "__main__":
    print("=== Example: Using Volume and VolumeFileStore classes ===")
    example_using_classes()
    
    print("\n=== Example: Using helper functions ===")
    example_using_helper_functions()
    
    print("\n=== Example: download_file_as_bytes method ===")
    example_download_file_as_bytes()
    
    print("\nAll examples completed successfully!")