"Utilities to work with volumes and files within the databricks workspace."
import os
from backend.auth import get_databricks_auth
from backend.config import get_config
from backend.logging import get_logger
from typing import Optional

app_config = get_config()
databricks_auth = get_databricks_auth()
logger = get_logger(__name__)

class VolumeHandler:
    """Handles operations related to Databricks volumes."""

    def __init__(
        self,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        volume_name: Optional[str] = None,
        client: Optional[object] = None,
    ):
        app_config = get_config()
        self.catalog = catalog if catalog is not None else app_config.databricks_catalog
        self.schema = schema if schema is not None else app_config.databricks_schema
        self.volume_name = volume_name if volume_name is not None else app_config.databricks_volume
        self.client = client or databricks_auth.get_workspace_client()

    def volume_exists(self) -> bool:
        """Checks if the volume exists in the databricks workspace."""
        full_name = f"{self.catalog}.{self.schema}.{self.volume_name}"
        try:
            self.client.volumes.read(name=full_name)
            return True
        except Exception as e:
            logger.warning(f"Volume {full_name} does not exist or cannot be accessed: {e}")
            return False

    def list_files(self) -> list[str]:
        """Lists the files in the volume."""
        volume_path = f"/Volumes/{self.catalog}/{self.schema}/{self.volume_name}"
        try:
            files = self.client.files.list_directory_contents(volume_path)
            return [item.path for item in files]
        except Exception as e:
            logger.error(f"Failed to list files in volume {self.volume_name}: {e}")
            return []

    def file_exists(self, file_name: str) -> bool:
        """Checks if a file exists in the volume using Files API get_metadata."""
        file_path = f"/Volumes/{self.catalog}/{self.schema}/{self.volume_name}/{file_name}"
        try:
            self.client.files.get_metadata(file_path)
            return True
        except Exception:
            return False

    def upload_file(self, file_path: str, overwrite: bool = False, destination_filename: Optional[str] = None):
        """Uploads a file to the volume using Files API upload.
        
        Args:
            file_path: Path to the local file to upload
            overwrite: Whether to overwrite existing files
            destination_filename: Optional filename to use in the volume. If not provided, uses the basename of file_path.
        """
        if not local_file_exists(file_path):
            logger.error(f"File {file_path} either does not exist or is not accessible.")
            return False
        file_name = destination_filename if destination_filename is not None else os.path.basename(file_path)
        volume_file_path = f"/Volumes/{self.catalog}/{self.schema}/{self.volume_name}/{file_name}"
        if self.file_exists(file_name) and not overwrite:
            logger.error(f"File {file_name} already exists in volume {self.volume_name} and overwrite is False.")
            return False
        try:
            with open(file_path, "rb") as f:
                self.client.files.upload(volume_file_path, f, overwrite=overwrite)
            return True
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to {volume_file_path}: {e}")
            return False

    def download_file(self, file_name: str, download_path: str):
        """Downloads a file from the volume onto the local filesystem using Files API download."""
        volume_file_path = f"/Volumes/{self.catalog}/{self.schema}/{self.volume_name}/{file_name}"
        try:
            resp = self.client.files.download(volume_file_path)
            with open(download_path, "wb") as f:
                f.write(resp.contents.read())
            return True
        except Exception as e:
            logger.error(f"Failed to download file {file_name} to {download_path}: {e}")
            return False

def local_file_exists(file_path: str) -> bool:
    """Checks if a file exists on the local filesystem."""
    return os.path.exists(file_path)


