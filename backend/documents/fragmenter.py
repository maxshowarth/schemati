"""Document fragmentation functionality for splitting pages into smaller fragments."""

import cv2
import numpy as np
from typing import List

from backend.documents.document import Page, PageFragment
from backend.config import get_config
from backend.logging import get_logger


logger = get_logger(__name__)


class Fragmenter:
    """Handles fragmentation of document pages into smaller rectangular fragments."""

    @staticmethod
    def tile_page(
        page: Page,
        tile_size: tuple[int, int] | None = None,
        overlap_ratio: float | None = None,
        complexity_threshold: float | None = None,
    ) -> List[PageFragment]:
        """Fragment a page into smaller rectangular tiles.
        
        Args:
            page: The page to fragment
            tile_size: Optional (width, height) tuple for tile dimensions
            overlap_ratio: Optional overlap ratio for tiles (0.0 to 1.0)
            complexity_threshold: Optional threshold for skipping blank tiles
            
        Returns:
            List of PageFragment objects
        """
        config = get_config()
        
        # Use provided parameters or fall back to config defaults
        if tile_size is None:
            tile_width = config.fragment_tile_width
            tile_height = config.fragment_tile_height
        else:
            tile_width, tile_height = tile_size
            
        if overlap_ratio is None:
            overlap_ratio = config.fragment_overlap_ratio
            
        if complexity_threshold is None:
            complexity_threshold = config.fragment_complexity_threshold
        
        # Decode the page image
        nparr = np.frombuffer(page.content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.warning(f"Failed to decode image for page {page.page_number}")
            return []
        
        height, width = image.shape[:2]
        logger.debug(f"Fragmenting page {page.page_number} with dimensions {width}x{height}")
        
        # Calculate step size with overlap
        step_width = int(tile_width * (1 - overlap_ratio))
        step_height = int(tile_height * (1 - overlap_ratio))
        
        fragments = []
        
        # Generate tiles
        for y in range(0, height, step_height):
            for x in range(0, width, step_width):
                # Calculate tile boundaries
                x1 = x
                y1 = y
                x2 = min(x + tile_width, width)
                y2 = min(y + tile_height, height)
                
                # Skip if tile is too small
                if (x2 - x1) < tile_width // 2 or (y2 - y1) < tile_height // 2:
                    continue
                
                # Extract tile
                tile = image[y1:y2, x1:x2]
                
                # Check complexity if threshold is set
                if complexity_threshold > 0:
                    complexity = Fragmenter._calculate_complexity(tile)
                    if complexity < complexity_threshold:
                        logger.debug(f"Skipping tile at ({x1}, {y1}) due to low complexity: {complexity:.3f}")
                        continue
                
                # Encode tile as JPEG
                success, encoded_tile = cv2.imencode('.jpg', tile)
                if not success:
                    logger.warning(f"Failed to encode tile at ({x1}, {y1})")
                    continue
                
                # Create fragment
                fragment = PageFragment(
                    content=encoded_tile.tobytes(),
                    bbox=[x1, y1, x2, y2]
                )
                fragments.append(fragment)
                
                logger.debug(f"Created fragment at ({x1}, {y1}, {x2}, {y2}) with complexity check")
        
        logger.info(f"Created {len(fragments)} fragments for page {page.page_number}")
        return fragments
    
    @staticmethod
    def _calculate_complexity(image: np.ndarray) -> float:
        """Calculate the visual complexity of an image.
        
        Uses the percentage of non-white pixels as a simple complexity metric.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Complexity score between 0.0 and 1.0
        """
        if image is None or image.size == 0:
            return 0.0
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Count non-white pixels (threshold at 240 to account for slight variations)
        non_white_pixels = np.sum(gray < 240)
        total_pixels = gray.size
        
        complexity = non_white_pixels / total_pixels if total_pixels > 0 else 0.0
        
        return complexity