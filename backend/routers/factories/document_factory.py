from pathlib import Path
import cv2
import numpy as np
import fitz  # PyMuPDF

from backend.models.document import Document, Page
from backend.routers.volume import VolumeHandler
from backend.config import get_config

app_config = get_config()

class DocumentFactory:
    """Factory class for creating Document objects from either a local path or Databricks volume."""

    def from_disk(self, path: Path) -> Document:
        """Creates a Document object from a local path."""
        return self._create_document(path)

    def from_databricks_volume(self, path: Path, volume_handler: VolumeHandler) -> Document:
        """Creates a Document object from a Databricks volume."""
        # TODO: Implement volume download logic here
        return self._create_document(path)

    def _create_document(self, path: Path) -> Document:
        """Creates a Document object from a local path handling multiple file types."""

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
        page = Page(page_number=1, bytes=cv2.imencode(".jpg", image)[1].tobytes())
        return Document(path=path, pages=[page])

    def _create_document_from_pdf(self, path: Path) -> Document:
        """Creates a Document object from a PDF file, potentially with multiple pages."""
        try:
            doc = fitz.open(str(path))
            pages = []
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=300)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                image_bytes = cv2.imencode(".jpg", img)[1].tobytes()
                pages.append(Page(page_number=i + 1, bytes=image_bytes))
            return Document(path=path, pages=pages)
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")
