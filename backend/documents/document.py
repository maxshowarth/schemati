from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel
from backend.config import get_config
from backend.databricks.auth import get_databricks_auth
from backend.logging import get_logger


app_config = get_config()
logger = get_logger(__name__)

class PageFragment:
    """Class that holds a fragment of a document."""

    def __init__(self, content: bytes, bbox: list[int]) -> None:
        self.bbox = bbox
        self.content = content

class PageMetadata(BaseModel):
    """Class that holds metadata for a page."""
    pass

class DocumentMetadata(BaseModel):
    """Class that holds metadata for a document."""
    pass

class Page:
    """Class that holds a page of a document."""
    def __init__(self, page_number: int, content: bytes) -> None:
        self.page_number = page_number
        self.content = content
        self.fragments: list[PageFragment] = []
        self.metadata: PageMetadata = PageMetadata()

    def fragment(
        self,
        tile_size: tuple[int, int] | None = None,
        overlap_ratio: float | None = None,
        complexity_threshold: float | None = None,
    ) -> list[PageFragment]:
        """Fragment this page into smaller rectangular tiles.
        
        This method uses the Fragmenter to create fragments and populates
        self.fragments with the results.
        
        Args:
            tile_size: Optional (width, height) tuple for tile dimensions
            overlap_ratio: Optional overlap ratio for tiles (0.0 to 1.0)
            complexity_threshold: Optional threshold for skipping blank tiles
            
        Returns:
            List of PageFragment objects (same as self.fragments)
        """
        # Import here to avoid circular imports
        from backend.documents.fragmenter import Fragmenter
        
        self.fragments = Fragmenter.tile_page(
            self, 
            tile_size=tile_size,
            overlap_ratio=overlap_ratio,
            complexity_threshold=complexity_threshold
        )
        return self.fragments

class Document:
    """Class that holds a document and its metadata.

    A document is a collection of pages. Each
    page is a collection of fragments. A page and its fragments are essentially an image that can
    be sent to an LLM for processing.
    """

    def __init__(self, path: Path, pages: list[Page]) -> None:
        self.path: Path = path
        self.pages: list[Page] = pages
        self.metadata: DocumentMetadata = DocumentMetadata()

