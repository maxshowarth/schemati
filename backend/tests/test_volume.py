import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from backend.routers.volume import VolumeHandler
from backend.config import set_config_for_test
from backend.exceptions import FileAlreadyExistsError, FileNotFoundError, VolumeUploadError

@pytest.fixture
def handler():
    return VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume", client=MagicMock())

def test_volume_exists_true(handler):
    mock_client = MagicMock()
    mock_client.volumes.read.return_value = MagicMock()
    handler.client = mock_client
    assert handler.volume_exists() is True
    mock_client.volumes.read.assert_called_once_with(name="test_catalog.test_schema.test_volume")

def test_volume_exists_false(handler):
    mock_client = MagicMock()
    mock_client.volumes.read.side_effect = Exception("Not found")
    handler.client = mock_client
    assert handler.volume_exists() is False

def test_list_files_success(handler):
    mock_client = MagicMock()
    mock_file1 = MagicMock(path="/Volumes/test_catalog/test_schema/test_volume/file1.txt")
    mock_file2 = MagicMock(path="/Volumes/test_catalog/test_schema/test_volume/file2.txt")
    mock_client.files.list_directory_contents.return_value = [mock_file1, mock_file2]
    handler.client = mock_client
    files = handler.list_files()
    assert files == [mock_file1.path, mock_file2.path]
    mock_client.files.list_directory_contents.assert_called_once()

def test_list_files_error(handler):
    mock_client = MagicMock()
    mock_client.files.list_directory_contents.side_effect = Exception("Error")
    handler.client = mock_client
    files = handler.list_files()
    assert files == []

def test_volumehandler_uses_config_defaults():
    set_config_for_test(
        databricks_catalog="default_catalog",
        databricks_schema="default_schema",
        databricks_volume="default_volume",
    )
    # Provide a mock client to avoid auth issues while still testing config defaults
    mock_client = MagicMock()
    vh = VolumeHandler(client=mock_client)
    assert vh.catalog == "default_catalog"
    assert vh.schema == "default_schema"
    assert vh.volume_name == "default_volume"

def test_upload_file_with_destination_filename():
    """Test that upload_file uses destination_filename when provided."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, prefix="tmptest_", suffix="_original.txt") as tmp_file:
        tmp_file.write(b"test content")
        tmp_file_path = tmp_file.name
    
    try:
        # Create handler with mock client
        handler = VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume", client=MagicMock())
        mock_client = handler.client
        
        # Mock file_exists to return False (file doesn't exist)
        mock_client.files.get_metadata.side_effect = Exception("Not found")
        
        # Call upload_file with destination_filename
        result = handler.upload_file(tmp_file_path, destination_filename="custom_name.txt")
        
        # Verify the upload was called with the custom filename
        expected_volume_path = "/Volumes/test_catalog/test_schema/test_volume/custom_name.txt"
        mock_client.files.upload.assert_called_once()
        args = mock_client.files.upload.call_args
        assert args[0][0] == expected_volume_path  # First positional argument should be the volume path
        assert result is True
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)

def test_upload_file_without_destination_filename():
    """Test that upload_file uses basename of file_path when destination_filename is not provided."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, prefix="tmptest_", suffix="_original.txt") as tmp_file:
        tmp_file.write(b"test content")
        tmp_file_path = tmp_file.name
    
    try:
        # Create handler with mock client
        handler = VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume", client=MagicMock())
        mock_client = handler.client
        
        # Mock file_exists to return False (file doesn't exist)
        mock_client.files.get_metadata.side_effect = Exception("Not found")
        
        # Call upload_file without destination_filename
        result = handler.upload_file(tmp_file_path)
        
        # Verify the upload was called with the basename of the temp file
        expected_filename = os.path.basename(tmp_file_path)
        expected_volume_path = f"/Volumes/test_catalog/test_schema/test_volume/{expected_filename}"
        mock_client.files.upload.assert_called_once()
        args = mock_client.files.upload.call_args
        assert args[0][0] == expected_volume_path  # First positional argument should be the volume path
        assert result is True
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)

def test_upload_file_raises_file_not_found_error():
    """Test that upload_file raises FileNotFoundError for non-existent local files."""
    handler = VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume", client=MagicMock())
    
    with pytest.raises(FileNotFoundError) as exc_info:
        handler.upload_file("/nonexistent/file.txt")
    
    assert exc_info.value.file_path == "/nonexistent/file.txt"
    assert "does not exist" in str(exc_info.value)

def test_upload_file_raises_file_already_exists_error():
    """Test that upload_file raises FileAlreadyExistsError when file exists and overwrite=False."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"test content")
        tmp_file_path = tmp_file.name
    
    try:
        # Create handler with mock client
        handler = VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume", client=MagicMock())
        mock_client = handler.client
        
        # Mock file_exists to return True (file exists)
        mock_client.files.get_metadata.return_value = MagicMock()
        
        # Call upload_file with overwrite=False (default)
        with pytest.raises(FileAlreadyExistsError) as exc_info:
            handler.upload_file(tmp_file_path, destination_filename="existing.txt")
        
        assert exc_info.value.filename == "existing.txt"
        assert exc_info.value.volume_name == "test_volume"
        assert "already exists" in str(exc_info.value)
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)

def test_upload_file_succeeds_with_overwrite():
    """Test that upload_file succeeds when file exists but overwrite=True."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"test content")
        tmp_file_path = tmp_file.name
    
    try:
        # Create handler with mock client
        handler = VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume", client=MagicMock())
        mock_client = handler.client
        
        # Mock file_exists to return True (file exists)
        mock_client.files.get_metadata.return_value = MagicMock()
        
        # Call upload_file with overwrite=True
        result = handler.upload_file(tmp_file_path, overwrite=True, destination_filename="existing.txt")
        
        # Should succeed and return True
        assert result is True
        mock_client.files.upload.assert_called_once()
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)

def test_upload_file_raises_volume_upload_error():
    """Test that upload_file raises VolumeUploadError when upload fails."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"test content")
        tmp_file_path = tmp_file.name
    
    try:
        # Create handler with mock client
        handler = VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume", client=MagicMock())
        mock_client = handler.client
        
        # Mock file_exists to return False (file doesn't exist)
        mock_client.files.get_metadata.side_effect = Exception("Not found")
        
        # Mock upload to raise an exception
        upload_error = Exception("Network timeout")
        mock_client.files.upload.side_effect = upload_error
        
        # Call upload_file
        with pytest.raises(VolumeUploadError) as exc_info:
            handler.upload_file(tmp_file_path, destination_filename="test.txt")
        
        assert exc_info.value.file_path == tmp_file_path
        assert "test.txt" in exc_info.value.volume_path
        assert exc_info.value.original_error is upload_error
        assert "Network timeout" in str(exc_info.value)
        
    finally:
        # Clean up
        os.unlink(tmp_file_path)