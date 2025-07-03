from pathlib import Path
from typing import List, Optional, Union

import cv2
import numpy as np
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

    def visualize_fragments(self, line_thickness: int = 2) -> bytes:
        """Create a visualization of the page with fragment bounding boxes overlaid.
        
        This method draws rectangles around each fragment on the original page image
        for visual debugging purposes.
        
        Args:
            line_thickness: Thickness of the bounding box lines
            
        Returns:
            JPEG-encoded image bytes with bounding boxes drawn
            
        Raises:
            ValueError: If the page content cannot be decoded as an image
        """
        # Decode the page image
        nparr = np.frombuffer(self.content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError(f"Failed to decode image for page {self.page_number}")
        
        # Create a copy to draw on
        viz_image = image.copy()
        
        # Draw bounding boxes for each fragment
        for i, fragment in enumerate(self.fragments):
            x1, y1, x2, y2 = fragment.bbox
            
            # Use different colors for different fragments (cycling through a palette)
            color_palette = [
                (0, 255, 0),    # Green
                (255, 0, 0),    # Blue
                (0, 0, 255),    # Red
                (255, 255, 0),  # Cyan
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Yellow
                (128, 0, 128),  # Purple
                (255, 165, 0),  # Orange
            ]
            color = color_palette[i % len(color_palette)]
            
            # Draw rectangle
            cv2.rectangle(viz_image, (x1, y1), (x2, y2), color, line_thickness)
            
            # Add fragment number label
            label = str(i + 1)
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(
                viz_image, 
                (x1, y1 - label_size[1] - 5), 
                (x1 + label_size[0] + 5, y1), 
                color, 
                -1
            )
            cv2.putText(
                viz_image, 
                label, 
                (x1 + 3, y1 - 3), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (255, 255, 255), 
                2
            )
        
        # Encode as JPEG
        success, encoded_image = cv2.imencode(".jpg", viz_image)
        if not success:
            raise ValueError(f"Failed to encode visualization for page {self.page_number}")
        
        return encoded_image.tobytes()

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

