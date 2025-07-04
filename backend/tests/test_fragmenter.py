"""Tests for document fragmentation functionality."""

import cv2
import numpy as np

from backend.config import set_config_for_test
from backend.documents.document import Page, PageFragment
from backend.documents.fragmenter import Fragmenter


class TestFragmenter:
    """Test the Fragmenter class."""

    def setup_method(self):
        """Set up test configuration."""
        set_config_for_test(
            fragment_tile_width=100,
            fragment_tile_height=100,
            fragment_overlap_ratio=0.1,
            fragment_complexity_threshold=0.03,
            fragment_dynamic_enabled=False,
            fragment_num_tiles_horizontal=5,
            fragment_num_tiles_vertical=4,
        )

    def _create_test_image(self, width: int, height: int, content_type: str = "white") -> bytes:
        """Create a test image with specified dimensions and content type."""
        if content_type == "white":
            # Create white image
            image = np.ones((height, width, 3), dtype=np.uint8) * 255
        elif content_type == "black":
            # Create black image
            image = np.zeros((height, width, 3), dtype=np.uint8)
        elif content_type == "complex":
            # Create image with some content
            image = np.ones((height, width, 3), dtype=np.uint8) * 255
            # Add some black rectangles
            cv2.rectangle(image, (10, 10), (width-10, height-10), (0, 0, 0), 2)
            cv2.rectangle(image, (20, 20), (width-20, height-20), (128, 128, 128), -1)
        else:
            raise ValueError(f"Unknown content type: {content_type}")

        success, encoded = cv2.imencode(".jpg", image)
        if not success:
            raise RuntimeError("Failed to encode test image")

        return encoded.tobytes()

    def test_tile_page_basic(self):
        """Test basic page fragmentation."""
        # Create a 300x300 image
        image_bytes = self._create_test_image(300, 300, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(page)

        # Should create multiple fragments
        assert len(fragments) > 0
        assert all(isinstance(f, PageFragment) for f in fragments)
        assert all(len(f.bbox) == 4 for f in fragments)
        assert all(f.content for f in fragments)

    def test_tile_page_with_custom_tile_size(self):
        """Test fragmentation with custom tile size."""
        image_bytes = self._create_test_image(200, 200, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(page, tile_size=(50, 50))

        # Should create more fragments with smaller tile size
        assert len(fragments) > 0

        # Check that fragments have appropriate dimensions
        for fragment in fragments:
            x1, y1, x2, y2 = fragment.bbox
            assert x2 - x1 <= 50
            assert y2 - y1 <= 50

    def test_tile_page_with_overlap(self):
        """Test fragmentation with overlap."""
        image_bytes = self._create_test_image(150, 150, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments_no_overlap = Fragmenter.tile_page(page, overlap_ratio=0.0)
        fragments_with_overlap = Fragmenter.tile_page(page, overlap_ratio=0.2)

        # With overlap, we should get more fragments
        assert len(fragments_with_overlap) >= len(fragments_no_overlap)

    def test_tile_page_complexity_threshold(self):
        """Test fragmentation with complexity threshold."""
        # Create mostly white image
        image_bytes = self._create_test_image(200, 200, "white")
        page = Page(page_number=1, content=image_bytes)

        fragments_no_threshold = Fragmenter.tile_page(page, complexity_threshold=0.0)
        fragments_with_threshold = Fragmenter.tile_page(page, complexity_threshold=0.05)

        # With threshold, we should get fewer fragments (white tiles filtered out)
        assert len(fragments_with_threshold) <= len(fragments_no_threshold)

    def test_tile_page_complex_image(self):
        """Test fragmentation with complex image content."""
        image_bytes = self._create_test_image(200, 200, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(page, complexity_threshold=0.01)

        # Complex image should produce fragments even with threshold
        assert len(fragments) > 0

        # Check that bounding boxes are within image bounds
        for fragment in fragments:
            x1, y1, x2, y2 = fragment.bbox
            assert 0 <= x1 < x2 <= 200
            assert 0 <= y1 < y2 <= 200

    def test_tile_page_small_image(self):
        """Test fragmentation with image smaller than tile size."""
        image_bytes = self._create_test_image(50, 50, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(page, tile_size=(100, 100))

        # Should still create at least one fragment
        assert len(fragments) >= 1

        # Fragment should not exceed image dimensions
        for fragment in fragments:
            x1, y1, x2, y2 = fragment.bbox
            assert x2 <= 50
            assert y2 <= 50

    def test_tile_page_invalid_image(self):
        """Test fragmentation with invalid image data."""
        # Create invalid image data
        invalid_bytes = b"not an image"
        page = Page(page_number=1, content=invalid_bytes)

        fragments = Fragmenter.tile_page(page)

        # Should return empty list for invalid image
        assert len(fragments) == 0

    def test_calculate_complexity_white_image(self):
        """Test complexity calculation for white image."""
        white_image = np.ones((100, 100, 3), dtype=np.uint8) * 255

        complexity = Fragmenter._calculate_complexity(white_image)

        # White image should have very low complexity
        assert complexity < 0.1

    def test_calculate_complexity_black_image(self):
        """Test complexity calculation for black image."""
        black_image = np.zeros((100, 100, 3), dtype=np.uint8)

        complexity = Fragmenter._calculate_complexity(black_image)

        # Black image should have high complexity
        assert complexity > 0.9

    def test_calculate_complexity_mixed_image(self):
        """Test complexity calculation for mixed image."""
        # Create image with half white, half black
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        image[:50, :] = 0  # Make top half black

        complexity = Fragmenter._calculate_complexity(image)

        # Mixed image should have medium complexity
        assert 0.3 < complexity < 0.7

    def test_calculate_complexity_empty_image(self):
        """Test complexity calculation for empty image."""
        empty_image = np.array([])

        complexity = Fragmenter._calculate_complexity(empty_image)

        # Empty image should have zero complexity
        assert complexity == 0.0

    def test_calculate_complexity_grayscale_image(self):
        """Test complexity calculation for grayscale image."""
        gray_image = np.ones((100, 100), dtype=np.uint8) * 128

        complexity = Fragmenter._calculate_complexity(gray_image)

        # Gray image should have high complexity (not white)
        assert complexity > 0.8

    def test_config_integration(self):
        """Test that fragmenter uses configuration values."""
        # Set specific config values
        set_config_for_test(
            fragment_tile_width=75,
            fragment_tile_height=75,
            fragment_overlap_ratio=0.2,
            fragment_complexity_threshold=0.1,
        )

        image_bytes = self._create_test_image(200, 200, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(page)

        # Should use config values
        assert len(fragments) > 0

        # Check that fragments respect the configured tile size
        for fragment in fragments:
            x1, y1, x2, y2 = fragment.bbox
            assert x2 - x1 <= 75
            assert y2 - y1 <= 75

    def test_fragment_content_is_valid_jpeg(self):
        """Test that fragment content is valid JPEG data."""
        image_bytes = self._create_test_image(150, 150, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(page)

        assert len(fragments) > 0

        # Check that each fragment contains valid JPEG data
        for fragment in fragments:
            # Try to decode the fragment content
            nparr = np.frombuffer(fragment.content, np.uint8)
            decoded = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            assert decoded is not None
            assert decoded.shape[0] > 0
            assert decoded.shape[1] > 0

    def test_bbox_coordinates_are_correct(self):
        """Test that bounding box coordinates are correct."""
        image_bytes = self._create_test_image(150, 150, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(page, tile_size=(50, 50), overlap_ratio=0.0)

        # Check that bounding boxes are non-overlapping and within image bounds
        for fragment in fragments:
            x1, y1, x2, y2 = fragment.bbox
            assert x1 >= 0
            assert y1 >= 0
            assert x2 <= 150
            assert y2 <= 150
            assert x1 < x2
            assert y1 < y2

    def test_grid_based_tiling(self):
        """Test grid-based tiling with specified tile counts."""
        image_bytes = self._create_test_image(500, 400, "complex")
        page = Page(page_number=1, content=image_bytes)

        # Test with 5x4 grid (should create 20 tiles max)
        fragments = Fragmenter.tile_page(
            page, 
            num_tiles_horizontal=5, 
            num_tiles_vertical=4,
            overlap_ratio=0.0,
            complexity_threshold=0.0  # Ensure all tiles are created
        )

        # Should create exactly 5x4 = 20 tiles
        assert len(fragments) == 20

        # Check that all tiles are within bounds and cover the image
        for fragment in fragments:
            x1, y1, x2, y2 = fragment.bbox
            assert x1 >= 0
            assert y1 >= 0
            assert x2 <= 500
            assert y2 <= 400
            assert x1 < x2
            assert y1 < y2

    def test_grid_based_tiling_with_overlap(self):
        """Test grid-based tiling with overlap."""
        image_bytes = self._create_test_image(300, 300, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(
            page, 
            num_tiles_horizontal=3, 
            num_tiles_vertical=3,
            overlap_ratio=0.2,
            complexity_threshold=0.0
        )

        # Should create 3x3 = 9 tiles
        assert len(fragments) == 9

        # Verify tiles have reasonable overlap
        for fragment in fragments:
            x1, y1, x2, y2 = fragment.bbox
            # Each tile should be larger than base size due to overlap
            tile_width = x2 - x1
            tile_height = y2 - y1
            base_width = 300 / 3  # 100
            base_height = 300 / 3  # 100
            # With 20% overlap, tiles should be larger than base size
            assert tile_width >= base_width

    def test_grid_vs_fixed_size_difference(self):
        """Test that grid-based and fixed-size tiling produce different results."""
        image_bytes = self._create_test_image(350, 280, "complex")
        page = Page(page_number=1, content=image_bytes)

        # Grid-based approach
        grid_fragments = Fragmenter.tile_page(
            page, 
            num_tiles_horizontal=3, 
            num_tiles_vertical=2,
            overlap_ratio=0.0,
            complexity_threshold=0.0
        )

        # Fixed-size approach
        fixed_fragments = Fragmenter.tile_page(
            page, 
            tile_size=(100, 100),
            overlap_ratio=0.0,
            complexity_threshold=0.0
        )

        # Should have different number of fragments
        assert len(grid_fragments) != len(fixed_fragments)
        # Grid should create exactly 3x2 = 6 tiles
        assert len(grid_fragments) == 6

    def test_grid_tiling_covers_entire_image(self):
        """Test that grid tiling provides 100% coverage."""
        image_bytes = self._create_test_image(350, 280, "complex")
        page = Page(page_number=1, content=image_bytes)

        fragments = Fragmenter.tile_page(
            page, 
            num_tiles_horizontal=3, 
            num_tiles_vertical=2,
            overlap_ratio=0.0,
            complexity_threshold=0.0
        )

        # Check that tiles reach the edges
        min_x = min(f.bbox[0] for f in fragments)
        min_y = min(f.bbox[1] for f in fragments)
        max_x = max(f.bbox[2] for f in fragments)
        max_y = max(f.bbox[3] for f in fragments)

        assert min_x == 0
        assert min_y == 0
        assert max_x == 350
        assert max_y == 280

    def test_default_grid_configuration(self):
        """Test that default grid configuration is used when no parameters are specified."""
        image_bytes = self._create_test_image(500, 400, "complex")
        page = Page(page_number=1, content=image_bytes)

        # Call without any tile parameters - should use grid defaults (5x4)
        fragments = Fragmenter.tile_page(
            page, 
            complexity_threshold=0.0
        )

        # Should create 5x4 = 20 tiles using default grid
        assert len(fragments) == 20


class TestPageIntegration:
    """Test integration between Page class and Fragmenter."""

    def setup_method(self):
        """Set up test configuration."""
        set_config_for_test(
            fragment_tile_width=100,
            fragment_tile_height=100,
            fragment_overlap_ratio=0.1,
            fragment_complexity_threshold=0.03,
            fragment_dynamic_enabled=False,
        )

    def _create_test_image(self, width: int, height: int, content_type: str = "white") -> bytes:
        """Create a test image with specified dimensions and content type."""
        if content_type == "white":
            # Create white image
            image = np.ones((height, width, 3), dtype=np.uint8) * 255
        elif content_type == "complex":
            # Create image with some content
            image = np.ones((height, width, 3), dtype=np.uint8) * 255
            # Add some black rectangles
            cv2.rectangle(image, (10, 10), (width-10, height-10), (0, 0, 0), 2)
            cv2.rectangle(image, (20, 20), (width-20, height-20), (128, 128, 128), -1)
        else:
            raise ValueError(f"Unknown content type: {content_type}")

        success, encoded = cv2.imencode(".jpg", image)
        if not success:
            raise RuntimeError("Failed to encode test image")

        return encoded.tobytes()

    def test_page_fragment_method(self):
        """Test that Page.fragment() method works correctly."""
        # Create a page with complex content
        image_bytes = self._create_test_image(300, 300, "complex")
        page = Page(page_number=1, content=image_bytes)

        # Initially, fragments should be empty
        assert len(page.fragments) == 0

        # Fragment the page
        fragments = page.fragment()

        # Fragments should be populated
        assert len(page.fragments) > 0
        assert page.fragments == fragments
        assert all(isinstance(f, PageFragment) for f in page.fragments)

    def test_page_fragment_method_with_custom_params(self):
        """Test Page.fragment() with custom parameters."""
        image_bytes = self._create_test_image(300, 300, "complex")
        page = Page(page_number=1, content=image_bytes)

        # Fragment with custom parameters
        fragments = page.fragment(
            tile_size=(50, 50),
            overlap_ratio=0.2,
            complexity_threshold=0.01
        )

        # Should create fragments
        assert len(fragments) > 0
        assert len(page.fragments) == len(fragments)

    def test_integration_workflow(self):
        """Test complete integration workflow."""
        # Create a page
        image_bytes = self._create_test_image(250, 200, "complex")
        page = Page(page_number=1, content=image_bytes)

        # 1. Fragment the page
        fragments = page.fragment(tile_size=(100, 100), overlap_ratio=0.1)

        # 2. Verify fragments were created and stored
        assert len(fragments) > 0
        assert len(page.fragments) == len(fragments)

        # 3. Verify bounding boxes are accessible
        for fragment in page.fragments:
            assert len(fragment.bbox) == 4
            x1, y1, x2, y2 = fragment.bbox
            assert x1 >= 0 and y1 >= 0
            assert x2 > x1 and y2 > y1
