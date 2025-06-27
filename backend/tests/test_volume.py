import pytest
from unittest.mock import MagicMock
from backend.routers.volume import VolumeHandler
from backend.config import set_config_for_test

@pytest.fixture
def handler():
    return VolumeHandler(catalog="test_catalog", schema="test_schema", volume_name="test_volume")

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
    vh = VolumeHandler()
    assert vh.catalog == "default_catalog"
    assert vh.schema == "default_schema"
    assert vh.volume_name == "default_volume"