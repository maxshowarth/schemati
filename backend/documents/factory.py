from pathlib import Path
import cv2
import numpy as np
import fitz  # PyMuPDF
import tempfile

from backend.documents.document import Document, Page
from backend.databricks.volume import Volume, VolumeFileStore
from backend.config import get_config

class DocumentFactory:
    """Factory class for creating Document objects from either a local path or Databricks volume."""

    def get_preview_data(self, path: Path) -> list[dict]:
        """Get preview data showing original and processed images for a file.
        
        Args:
            path: Path to the file to preview
            
        Returns:
            List of dictionaries containing original and processed image data.
            Each dict has keys: 'page_number', 'original_image', 'processed_image', 'was_resized'
        """
        app_config = get_config()
        
        if path.suffix.lower() in app_config.allowed_image_extensions:
            return self._get_image_preview_data(path)
        elif path.suffix.lower() in app_config.allowed_pdf_extensions:
            return self._get_pdf_preview_data(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    def _get_image_preview_data(self, path: Path) -> list[dict]:
        """Get preview data for a single image file."""
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"Failed to read image from path: {path}")
        
        # Get original and processed images
        original_image = image.copy()
        processed_image = self._resize_image_if_needed(image)
        
        # Check if resizing occurred
        was_resized = not np.array_equal(original_image, processed_image)
        
        return [{
            'page_number': 1,
            'original_image': original_image,
            'processed_image': processed_image,
            'was_resized': was_resized
        }]

    def _get_pdf_preview_data(self, path: Path) -> list[dict]:
        """Get preview data for a PDF file."""
        app_config = get_config()
        preview_data = []
        
        try:
            doc = fitz.open(str(path))
            for i, page in enumerate(doc):
                # Convert page to image
                pix = page.get_pixmap(dpi=app_config.image_dpi)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                
                # Get original and processed images
                original_image = img.copy()
                processed_image = self._resize_image_if_needed(img)
                
                # Check if resizing occurred
                was_resized = not np.array_equal(original_image, processed_image)
                
                preview_data.append({
                    'page_number': i + 1,
                    'original_image': original_image,
                    'processed_image': processed_image,
                    'was_resized': was_resized
                })
            
            return preview_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to preview PDF: {e}")

    def _resize_image_if_needed(self, image: np.ndarray) -> np.ndarray:
        """Resize image if it exceeds maximum dimensions while preserving aspect ratio."""
        app_config = get_config()  # Get config dynamically
        height, width = image.shape[:2]
        max_width = app_config.image_max_width
        max_height = app_config.image_max_height
        
        if width <= max_width and height <= max_height:
            return image
            
        # Calculate scaling factor to fit within max dimensions
        width_ratio = max_width / width
        height_ratio = max_height / height
        scale_factor = min(width_ratio, height_ratio)
        
        # Calculate new dimensions
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # Resize the image
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized

    def from_disk(self, path: Path) -> Document:
        """Creates a Document object from a local path."""
        return self._create_document(path)

    def from_databricks_volume(self, file_name: str, file_store: VolumeFileStore) -> Document:
        """Creates a Document object from a file in a Databricks volume.

        Args:
            file_name: The name of the file in the Databricks volume.
            file_store: An instance of VolumeFileStore for accessing the volume.

        Returns:
            Document: The created Document object from the downloaded file.
        """
        app_config = get_config()  # Get config dynamically
        suffix = Path(file_name).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp_file:
            file_store.download_file(file_name, tmp_file.name)
            tmp_path = Path(tmp_file.name)
            if suffix in app_config.allowed_image_extensions:
                return self._create_document_from_image(tmp_path)
            elif suffix in app_config.allowed_pdf_extensions:
                return self._create_document_from_pdf(tmp_path)
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

    def _create_document(self, path: Path) -> Document:
        """Creates a Document object from a local path handling multiple file types."""
        app_config = get_config()  # Get config dynamically

        if path.suffix.lower() in app_config.allowed_image_extensions:
            return self._create_document_from_image(path)
        elif path.suffix.lower() in app_config.allowed_pdf_extensions:
            return self._create_document_from_pdf(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    def _create_document_from_image(self, path: Path) -> Document:
        """Creates a Document object from a single image file."""
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f"Failed to read image from path: {path}")
        
        # Resize image if it exceeds maximum dimensions
        resized_image = self._resize_image_if_needed(image)
        
        page = Page(page_number=1, content=cv2.imencode(".jpg", resized_image)[1].tobytes())
        return Document(path=path, pages=[page])

    def _create_document_from_pdf(self, path: Path) -> Document:
        """Creates a Document object from a PDF file, potentially with multiple pages."""
        app_config = get_config()  # Get config dynamically
        try:
            doc = fitz.open(str(path))
            pages = []
            for i, page in enumerate(doc):
                # Use configurable DPI instead of hardcoded 300
                pix = page.get_pixmap(dpi=app_config.image_dpi)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                
                # Resize image if it exceeds maximum dimensions
                resized_img = self._resize_image_if_needed(img)
                
                image_content = cv2.imencode(".jpg", resized_img)[1].tobytes()
                pages.append(Page(page_number=i + 1, content=image_content))
            return Document(path=path, pages=pages)
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")
