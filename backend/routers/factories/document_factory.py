from pathlib import Path
import cv2
import numpy as np
import fitz  # PyMuPDF
import tempfile

from backend.models.document import Document, Page
from backend.routers.volume import Volume, VolumeFileStore
from backend.config import get_config

app_config = get_config()

class DocumentFactory:
    """Factory class for creating Document objects from either a local path or Databricks volume."""

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
        page = Page(page_number=1, content=cv2.imencode(".jpg", image)[1].tobytes())
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
                image_content = cv2.imencode(".jpg", img)[1].tobytes()
                pages.append(Page(page_number=i + 1, content=image_content))
            return Document(path=path, pages=pages)
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF to images: {e}")
