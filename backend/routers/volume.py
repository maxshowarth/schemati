"Utilities to work with volumes and files within the databricks workspace."
import os
from typing import Optional
from pydantic import BaseModel, ConfigDict
from databricks.sdk import WorkspaceClient

from backend.auth import get_databricks_auth
from backend.config import get_config
from backend.logging import get_logger
from backend.exceptions import FileAlreadyExistsError, FileNotFoundError, VolumeUploadError

logger = get_logger(__name__)


class Volume(BaseModel):
    """Represents a Databricks volume identity (catalog, schema, name).
    
    This is a pure pydantic model that contains only the logical identity
    of a volume and can construct volume-based URIs. It does not perform
    any I/O operations or interact with the Databricks API.
    """
    model_config = ConfigDict(extra='forbid')
    
    catalog: str
    schema_name: str
    volume_name: str
    
    def get_full_name(self) -> str:
        """Return the full volume name in format: catalog.schema.volume_name"""
        return f"{self.catalog}.{self.schema_name}.{self.volume_name}"
    
    def get_volume_path(self) -> str:
        """Return the volume path in format: /Volumes/catalog/schema/volume_name"""
        return f"/Volumes/{self.catalog}/{self.schema_name}/{self.volume_name}"
    
    def get_file_path(self, file_name: str) -> str:
        """Return the full file path for a given file name within this volume."""
        return f"{self.get_volume_path()}/{file_name}"


class VolumeFileStore:
    """Handles file operations for a Databricks volume.
    
    This class is responsible for interacting with the Databricks workspace
    to list files, check existence, upload, and download content from a volume.
    It is constructed with a Volume instance and a Databricks WorkspaceClient.
    """
    
    def __init__(self, volume: Volume, client: WorkspaceClient):
        """Initialize the VolumeFileStore with a Volume and WorkspaceClient.
        
        Args:
            volume: The Volume instance representing the volume identity
            client: The Databricks WorkspaceClient for API operations
        """
        self.volume = volume
        self.client = client
    
    def volume_exists(self) -> bool:
        """Checks if the volume exists in the databricks workspace."""
        full_name = self.volume.get_full_name()
        try:
            self.client.volumes.read(name=full_name)
            return True
        except Exception as e:
            logger.warning(f"Volume {full_name} does not exist or cannot be accessed: {e}")
            return False
    
    def list_files(self) -> list[str]:
        """Lists the files in the volume."""
        volume_path = self.volume.get_volume_path()
        try:
            files = self.client.files.list_directory_contents(volume_path)
            return [item.path for item in files]
        except Exception as e:
            logger.error(f"Failed to list files in volume {self.volume.volume_name}: {e}")
            return []
    
    def file_exists(self, file_name: str) -> bool:
        """Checks if a file exists in the volume using Files API get_metadata."""
        file_path = self.volume.get_file_path(file_name)
        try:
            self.client.files.get_metadata(file_path)
            return True
        except Exception:
            return False
    
    def upload_file(self, file_path: str, overwrite: bool = False, destination_filename: Optional[str] = None) -> bool:
        """Uploads a file to the volume using Files API upload.
        
        Args:
            file_path: Path to the local file to upload
            overwrite: Whether to overwrite existing files
            destination_filename: Optional filename to use in the volume. If not provided, uses the basename of file_path.
            
        Returns:
            True if upload was successful
            
        Raises:
            FileNotFoundError: If the local file doesn't exist
            FileAlreadyExistsError: If the file already exists in the volume and overwrite is False
            VolumeUploadError: If there's an error during the upload process
        """
        if not local_file_exists(file_path):
            logger.error(f"File {file_path} either does not exist or is not accessible.")
            raise FileNotFoundError(file_path)
            
        file_name = destination_filename if destination_filename is not None else os.path.basename(file_path)
        volume_file_path = self.volume.get_file_path(file_name)
        
        if self.file_exists(file_name) and not overwrite:
            logger.error(f"File {file_name} already exists in volume {self.volume.volume_name} and overwrite is False.")
            raise FileAlreadyExistsError(file_name, self.volume.volume_name)
            
        try:
            with open(file_path, "rb") as f:
                self.client.files.upload(volume_file_path, f, overwrite=overwrite)
            return True
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to {volume_file_path}: {e}")
            raise VolumeUploadError(file_path, volume_file_path, e)
    
    def download_file(self, file_name: str, download_path: str) -> bool:
        """Downloads a file from the volume onto the local filesystem using Files API download."""
        volume_file_path = self.volume.get_file_path(file_name)
        try:
            resp = self.client.files.download(volume_file_path)
            with open(download_path, "wb") as f:
                f.write(resp.contents.read())
            return True
        except Exception as e:
            logger.error(f"Failed to download file {file_name} to {download_path}: {e}")
            return False
    
    def download_file_as_bytes(self, file_name: str) -> bytes:
        """Downloads a file from the volume as bytes.
        
        Args:
            file_name: Name of the file to download
            
        Returns:
            The file content as bytes
            
        Raises:
            Exception: If the download fails
        """
        volume_file_path = self.volume.get_file_path(file_name)
        try:
            resp = self.client.files.download(volume_file_path)
            return resp.contents.read()
        except Exception as e:
            logger.error(f"Failed to download file {file_name} as bytes: {e}")
            raise


def create_volume_from_config(catalog: Optional[str] = None, schema: Optional[str] = None, volume_name: Optional[str] = None) -> Volume:
    """Create a Volume instance using configuration defaults.
    
    Args:
        catalog: Optional catalog override
        schema: Optional schema override  
        volume_name: Optional volume name override
        
    Returns:
        Volume instance with values from config or provided overrides
    """
    app_config = get_config()
    return Volume(
        catalog=catalog if catalog is not None else app_config.databricks_catalog,
        schema_name=schema if schema is not None else app_config.databricks_schema,
        volume_name=volume_name if volume_name is not None else app_config.databricks_volume
    )


def create_volume_file_store_from_config(catalog: Optional[str] = None, schema: Optional[str] = None, volume_name: Optional[str] = None, client: Optional[WorkspaceClient] = None) -> VolumeFileStore:
    """Create a VolumeFileStore instance using configuration defaults.
    
    Args:
        catalog: Optional catalog override
        schema: Optional schema override  
        volume_name: Optional volume name override
        client: Optional WorkspaceClient override
        
    Returns:
        VolumeFileStore instance with values from config or provided overrides
    """
    volume = create_volume_from_config(catalog, schema, volume_name)
    databricks_client = client if client is not None else get_databricks_auth().get_workspace_client()
    return VolumeFileStore(volume, databricks_client)





def local_file_exists(file_path: str) -> bool:
    """Checks if a file exists on the local filesystem."""
    return os.path.exists(file_path)


