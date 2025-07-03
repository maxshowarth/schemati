import pytest
import tempfile
import os
from unittest.mock import MagicMock
from backend.routers.volume import Volume, VolumeFileStore, create_volume_from_config, create_volume_file_store_from_config
from backend.config import set_config_for_test
from backend.exceptions import FileAlreadyExistsError, FileNotFoundError, VolumeUploadError


class TestVolume:
    """Test the Volume pydantic model."""

    def test_volume_creation(self):
        """Test creating a Volume instance."""
        volume = Volume(catalog="test_catalog", schema_name="test_schema", volume_name="test_volume")
        assert volume.catalog == "test_catalog"
        assert volume.schema_name == "test_schema"
        assert volume.volume_name == "test_volume"

    def test_get_full_name(self):
        """Test the get_full_name method."""
        volume = Volume(catalog="catalog", schema_name="schema", volume_name="volume")
        assert volume.get_full_name() == "catalog.schema.volume"

    def test_get_volume_path(self):
        """Test the get_volume_path method."""
        volume = Volume(catalog="catalog", schema_name="schema", volume_name="volume")
        assert volume.get_volume_path() == "/Volumes/catalog/schema/volume"

    def test_get_file_path(self):
        """Test the get_file_path method."""
        volume = Volume(catalog="catalog", schema_name="schema", volume_name="volume")
        assert volume.get_file_path("test.txt") == "/Volumes/catalog/schema/volume/test.txt"

    def test_volume_validation(self):
        """Test that Volume validates required fields."""
        with pytest.raises(ValueError):
            Volume(catalog="test", schema_name="test")  # Missing volume_name


class TestVolumeFileStore:
    """Test the VolumeFileStore class."""

    @pytest.fixture
    def volume(self):
        return Volume(catalog="test_catalog", schema_name="test_schema", volume_name="test_volume")

    @pytest.fixture
    def mock_client(self):
        return MagicMock()

    @pytest.fixture
    def file_store(self, volume, mock_client):
        return VolumeFileStore(volume, mock_client)

    def test_volume_file_store_creation(self, volume, mock_client):
        """Test creating a VolumeFileStore instance."""
        file_store = VolumeFileStore(volume, mock_client)
        assert file_store.volume == volume
        assert file_store.client == mock_client

    def test_volume_exists_true(self, file_store):
        """Test volume_exists returns True when volume exists."""
        file_store.client.volumes.read.return_value = MagicMock()
        assert file_store.volume_exists() is True
        file_store.client.volumes.read.assert_called_once_with(name="test_catalog.test_schema.test_volume")

    def test_volume_exists_false(self, file_store):
        """Test volume_exists returns False when volume doesn't exist."""
        file_store.client.volumes.read.side_effect = Exception("Not found")
        assert file_store.volume_exists() is False

    def test_list_files_success(self, file_store):
        """Test list_files returns file paths when successful."""
        mock_file1 = MagicMock(path="/Volumes/test_catalog/test_schema/test_volume/file1.txt")
        mock_file2 = MagicMock(path="/Volumes/test_catalog/test_schema/test_volume/file2.txt")
        file_store.client.files.list_directory_contents.return_value = [mock_file1, mock_file2]

        files = file_store.list_files()
        assert files == [mock_file1.path, mock_file2.path]
        file_store.client.files.list_directory_contents.assert_called_once_with("/Volumes/test_catalog/test_schema/test_volume")

    def test_list_files_error(self, file_store):
        """Test list_files returns empty list on error."""
        file_store.client.files.list_directory_contents.side_effect = Exception("Error")
        files = file_store.list_files()
        assert files == []

    def test_file_exists_true(self, file_store):
        """Test file_exists returns True when file exists."""
        file_store.client.files.get_metadata.return_value = MagicMock()
        assert file_store.file_exists("test.txt") is True
        file_store.client.files.get_metadata.assert_called_once_with("/Volumes/test_catalog/test_schema/test_volume/test.txt")

    def test_file_exists_false(self, file_store):
        """Test file_exists returns False when file doesn't exist."""
        file_store.client.files.get_metadata.side_effect = Exception("Not found")
        assert file_store.file_exists("test.txt") is False

    def test_upload_file_with_destination_filename(self, file_store):
        """Test that upload_file uses destination_filename when provided."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, prefix="tmptest_", suffix="_original.txt") as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name

        try:
            # Mock file_exists to return False (file doesn't exist)
            file_store.client.files.get_metadata.side_effect = Exception("Not found")

            # Call upload_file with destination_filename
            result = file_store.upload_file(tmp_file_path, destination_filename="custom_name.txt")

            # Verify the upload was called with the custom filename
            expected_volume_path = "/Volumes/test_catalog/test_schema/test_volume/custom_name.txt"
            file_store.client.files.upload.assert_called_once()
            args = file_store.client.files.upload.call_args
            assert args[0][0] == expected_volume_path  # First positional argument should be the volume path
            assert result is True

        finally:
            # Clean up
            os.unlink(tmp_file_path)

    def test_upload_file_without_destination_filename(self, file_store):
        """Test that upload_file uses basename of file_path when destination_filename is not provided."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, prefix="tmptest_", suffix="_original.txt") as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name

        try:
            # Mock file_exists to return False (file doesn't exist)
            file_store.client.files.get_metadata.side_effect = Exception("Not found")

            # Call upload_file without destination_filename
            result = file_store.upload_file(tmp_file_path)

            # Verify the upload was called with the basename of the temp file
            expected_filename = os.path.basename(tmp_file_path)
            expected_volume_path = f"/Volumes/test_catalog/test_schema/test_volume/{expected_filename}"
            file_store.client.files.upload.assert_called_once()
            args = file_store.client.files.upload.call_args
            assert args[0][0] == expected_volume_path  # First positional argument should be the volume path
            assert result is True

        finally:
            # Clean up
            os.unlink(tmp_file_path)

    def test_upload_file_raises_file_not_found_error(self, file_store):
        """Test that upload_file raises FileNotFoundError for non-existent local files."""
        with pytest.raises(FileNotFoundError) as exc_info:
            file_store.upload_file("/nonexistent/file.txt")

        assert exc_info.value.file_path == "/nonexistent/file.txt"
        assert "does not exist" in str(exc_info.value)

    def test_upload_file_raises_file_already_exists_error(self, file_store):
        """Test that upload_file raises FileAlreadyExistsError when file exists and overwrite=False."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name

        try:
            # Mock file_exists to return True (file exists)
            file_store.client.files.get_metadata.return_value = MagicMock()

            # Call upload_file with overwrite=False (default)
            with pytest.raises(FileAlreadyExistsError) as exc_info:
                file_store.upload_file(tmp_file_path, destination_filename="existing.txt")

            assert exc_info.value.filename == "existing.txt"
            assert exc_info.value.volume_name == "test_volume"
            assert "already exists" in str(exc_info.value)

        finally:
            # Clean up
            os.unlink(tmp_file_path)

    def test_upload_file_succeeds_with_overwrite(self, file_store):
        """Test that upload_file succeeds when file exists but overwrite=True."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name

        try:
            # Mock file_exists to return True (file exists)
            file_store.client.files.get_metadata.return_value = MagicMock()

            # Call upload_file with overwrite=True
            result = file_store.upload_file(tmp_file_path, overwrite=True, destination_filename="existing.txt")

            # Should succeed and return True
            assert result is True
            file_store.client.files.upload.assert_called_once()

        finally:
            # Clean up
            os.unlink(tmp_file_path)

    def test_upload_file_raises_volume_upload_error(self, file_store):
        """Test that upload_file raises VolumeUploadError when upload fails."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_file_path = tmp_file.name

        try:
            # Mock file_exists to return False (file doesn't exist)
            file_store.client.files.get_metadata.side_effect = Exception("Not found")

            # Mock upload to raise an exception
            upload_error = Exception("Network timeout")
            file_store.client.files.upload.side_effect = upload_error

            # Call upload_file
            with pytest.raises(VolumeUploadError) as exc_info:
                file_store.upload_file(tmp_file_path, destination_filename="test.txt")

            assert exc_info.value.file_path == tmp_file_path
            assert "test.txt" in exc_info.value.volume_path
            assert exc_info.value.original_error is upload_error
            assert "Network timeout" in str(exc_info.value)

        finally:
            # Clean up
            os.unlink(tmp_file_path)

    def test_download_file_success(self, file_store):
        """Test download_file successful download."""
        mock_response = MagicMock()
        mock_response.contents.read.return_value = b"file content"
        file_store.client.files.download.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            download_path = tmp_file.name

        try:
            result = file_store.download_file("test.txt", download_path)
            assert result is True
            file_store.client.files.download.assert_called_once_with("/Volumes/test_catalog/test_schema/test_volume/test.txt")

            # Verify file was written
            with open(download_path, "rb") as f:
                content = f.read()
            assert content == b"file content"

        finally:
            os.unlink(download_path)


class TestHelperFunctions:
    """Test the helper functions."""

    def test_create_volume_from_config(self):
        """Test create_volume_from_config uses config defaults."""
        set_config_for_test(
            databricks_catalog="default_catalog",
            databricks_schema="default_schema",
            databricks_volume="default_volume",
        )

        volume = create_volume_from_config()
        assert volume.catalog == "default_catalog"
        assert volume.schema_name == "default_schema"
        assert volume.volume_name == "default_volume"

    def test_create_volume_from_config_with_overrides(self):
        """Test create_volume_from_config with parameter overrides."""
        set_config_for_test(
            databricks_catalog="config_catalog",
            databricks_schema="config_schema",
            databricks_volume="config_volume"
        )

        volume = create_volume_from_config(catalog="override_catalog", schema="override_schema")
        assert volume.catalog == "override_catalog"
        assert volume.schema_name == "override_schema"
        assert volume.volume_name == "config_volume"  # Should use config default

    def test_create_volume_file_store_from_config(self):
        """Test create_volume_file_store_from_config with mock client."""
        set_config_for_test(
            databricks_catalog="config_catalog",
            databricks_schema="config_schema",
            databricks_volume="config_volume"
        )

        mock_client = MagicMock()
        file_store = create_volume_file_store_from_config(client=mock_client)

        assert file_store.volume.catalog == "config_catalog"
        assert file_store.volume.schema_name == "config_schema"
        assert file_store.volume.volume_name == "config_volume"
        assert file_store.client == mock_client