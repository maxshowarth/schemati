"""Custom exceptions for Schemati backend operations."""


class VolumeError(Exception):
    """Base exception for volume-related operations."""
    pass


class FileAlreadyExistsError(VolumeError):
    """Raised when trying to upload a file that already exists and overwrite is False."""
    
    def __init__(self, filename: str, volume_name: str):
        self.filename = filename
        self.volume_name = volume_name
        super().__init__(f"File '{filename}' already exists in volume '{volume_name}' and overwrite is disabled")


class FileNotFoundError(VolumeError):
    """Raised when trying to upload a file that doesn't exist locally."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Local file '{file_path}' does not exist or is not accessible")


class VolumeUploadError(VolumeError):
    """Raised when there's an error during the actual upload process."""
    
    def __init__(self, file_path: str, volume_path: str, original_error: Exception):
        self.file_path = file_path
        self.volume_path = volume_path
        self.original_error = original_error
        super().__init__(f"Failed to upload file '{file_path}' to '{volume_path}': {original_error}")