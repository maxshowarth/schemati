from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel
from backend.config import get_config
from backend.auth import get_databricks_auth
from backend.logging import get_logger


app_config = get_config()
logger = get_logger(__name__)

class PageFragment:
    """Class that holds a fragment of a document."""

    def __init__(self, bytes: bytes, bbox: list[int]) -> None:
        self.bbox = bbox
        self.bytes = bytes

class PageMetadata(BaseModel):
    """Class that holds metadata for a page."""
    pass

class DocumentMetadata(BaseModel):
    """Class that holds metadata for a document."""
    pass

class Page:
    """Class that holds a page of a document."""
    def __init__(self, page_number: int, bytes: bytes) -> None:
        self.page_number = page_number
        self.bytes = bytes
        self.fragments: list[PageFragment] = []
        self.metadata: PageMetadata = PageMetadata()

class Document:
    """Class that holds a document and it's metadata.

    A document is a collection of pages. Each
    page is a collection of fragments. A page and it's fragments are essentially an image that can
    be sent to an LLM for processing.
    """

    def __init__(self, path: Path, pages: list[Page]) -> None:
        self.path: Path = path
        self.pages: list[Page] = pages
        self.metadata: DocumentMetadata = DocumentMetadata()

