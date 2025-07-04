"""Document fragmentation functionality for splitting pages into smaller fragments."""


import cv2
import numpy as np

from backend.config import get_config
from backend.documents.document import Page, PageFragment
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
        num_tiles_horizontal: int | None = None,
        num_tiles_vertical: int | None = None,
    ) -> list[PageFragment]:
        """Fragment a page into smaller rectangular tiles.
        
        Args:
            page: The page to fragment
            tile_size: Optional (width, height) tuple for tile dimensions
            overlap_ratio: Optional overlap ratio for tiles (0.0 to 1.0)
            complexity_threshold: Optional threshold for skipping blank tiles
            num_tiles_horizontal: Optional number of tiles horizontally (overrides tile_size)
            num_tiles_vertical: Optional number of tiles vertically (overrides tile_size)
            
        Returns:
            List of PageFragment objects

        """
        config = get_config()

        # Use provided parameters or fall back to config defaults
        if num_tiles_horizontal is None:
            num_tiles_horizontal = config.fragment_num_tiles_horizontal
        if num_tiles_vertical is None:
            num_tiles_vertical = config.fragment_num_tiles_vertical

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

        fragments = []

        # Use grid-based tiling if num_tiles are specified, otherwise use tile_size approach
        if tile_size is None:
            # Grid-based tiling: divide image into approximately equal tiles
            fragments = Fragmenter._create_grid_tiles(
                image, width, height, num_tiles_horizontal, num_tiles_vertical,
                overlap_ratio, complexity_threshold, page.page_number
            )
        else:
            # Legacy tile_size approach for backward compatibility
            tile_width, tile_height = tile_size
            fragments = Fragmenter._create_fixed_size_tiles(
                image, width, height, tile_width, tile_height,
                overlap_ratio, complexity_threshold, page.page_number
            )

        logger.info(f"Created {len(fragments)} fragments for page {page.page_number}")
        return fragments

    @staticmethod
    def _create_grid_tiles(
        image: np.ndarray,
        width: int,
        height: int,
        num_tiles_horizontal: int,
        num_tiles_vertical: int,
        overlap_ratio: float,
        complexity_threshold: float,
        page_number: int,
    ) -> list[PageFragment]:
        """Create tiles using grid-based approach with approximately equal sizes."""
        fragments = []
        
        # Calculate base tile dimensions
        base_tile_width = width / num_tiles_horizontal
        base_tile_height = height / num_tiles_vertical
        
        # Calculate overlap in pixels
        overlap_width = base_tile_width * overlap_ratio
        overlap_height = base_tile_height * overlap_ratio
        
        for row in range(num_tiles_vertical):
            for col in range(num_tiles_horizontal):
                # Calculate tile boundaries with overlap
                x1 = max(0, int(col * base_tile_width - overlap_width))
                y1 = max(0, int(row * base_tile_height - overlap_height))
                x2 = min(width, int((col + 1) * base_tile_width + overlap_width))
                y2 = min(height, int((row + 1) * base_tile_height + overlap_height))
                
                # Ensure tiles cover the entire image (adjust last tiles to reach edges)
                if col == num_tiles_horizontal - 1:
                    x2 = width
                if row == num_tiles_vertical - 1:
                    y2 = height
                
                # Extract tile
                tile = image[y1:y2, x1:x2]
                
                # Skip empty tiles
                if tile.size == 0:
                    continue
                
                # Check complexity if threshold is set
                if complexity_threshold > 0:
                    complexity = Fragmenter._calculate_complexity(tile)
                    if complexity < complexity_threshold:
                        logger.debug(
                            "Skipping tile at (%s, %s) due to low complexity: %.3f", 
                            x1, y1, complexity
                        )
                        continue
                
                # Encode tile as JPEG
                success, encoded_tile = cv2.imencode(".jpg", tile)
                if not success:
                    logger.warning(f"Failed to encode tile at ({x1}, {y1})")
                    continue
                
                # Create fragment
                fragment = PageFragment(
                    content=encoded_tile.tobytes(),
                    bbox=[x1, y1, x2, y2],
                )
                fragments.append(fragment)
                
                logger.debug(f"Created grid tile at ({x1}, {y1}, {x2}, {y2}) [row {row}, col {col}]")
        
        return fragments

    @staticmethod
    def _create_fixed_size_tiles(
        image: np.ndarray,
        width: int,
        height: int,
        tile_width: int,
        tile_height: int,
        overlap_ratio: float,
        complexity_threshold: float,
        page_number: int,
    ) -> list[PageFragment]:
        """Create tiles using fixed tile size approach (legacy behavior)."""
        fragments = []
        
        # Calculate step size with overlap
        step_width = int(tile_width * (1 - overlap_ratio))
        step_height = int(tile_height * (1 - overlap_ratio))
        
        # Generate tiles
        for y in range(0, height, step_height):
            for x in range(0, width, step_width):
                # Calculate tile boundaries
                x1 = x
                y1 = y
                x2 = min(x + tile_width, width)
                y2 = min(y + tile_height, height)

                # Skip if tile is too small, unless we want 100% coverage (complexity_threshold == 0)
                if complexity_threshold > 0 and ((x2 - x1) < tile_width // 2 or (y2 - y1) < tile_height // 2):
                    continue

                # Extract tile
                tile = image[y1:y2, x1:x2]

                # Check complexity if threshold is set
                if complexity_threshold > 0:
                    complexity = Fragmenter._calculate_complexity(tile)
                    if complexity < complexity_threshold:
                        logger.debug(
                            "Skipping tile at (%s, %s) due to low complexity: %.3f", 
                            x1, y1, complexity
                        )
                        continue

                # Encode tile as JPEG
                success, encoded_tile = cv2.imencode(".jpg", tile)
                if not success:
                    logger.warning(f"Failed to encode tile at ({x1}, {y1})")
                    continue

                # Create fragment
                fragment = PageFragment(
                    content=encoded_tile.tobytes(),
                    bbox=[x1, y1, x2, y2],
                )
                fragments.append(fragment)

                logger.debug(f"Created fixed tile at ({x1}, {y1}, {x2}, {y2})")
        
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
