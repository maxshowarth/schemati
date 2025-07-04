#!/usr/bin/env python3
"""Test script for tile boundary visualization functionality."""

import numpy as np
import cv2
import sys
from pathlib import Path

# Add the parent directory to sys.path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from frontend.app import draw_tile_boundaries


class MockFragment:
    """Mock fragment for testing."""
    def __init__(self, bbox):
        self.bbox = bbox


def test_draw_tile_boundaries():
    """Test the draw_tile_boundaries function."""
    
    # Create test image
    test_image = np.ones((200, 300, 3), dtype=np.uint8) * 255  # White image
    
    # Test with empty fragments
    result = draw_tile_boundaries(test_image, [])
    assert result.shape == test_image.shape
    assert np.array_equal(result, test_image)  # Should be unchanged
    print("✅ Empty fragments test passed")
    
    # Test with one fragment
    fragments = [MockFragment([10, 10, 50, 50])]
    result = draw_tile_boundaries(test_image, fragments)
    assert result.shape == test_image.shape
    # Check that the image is modified (boundary drawn)
    assert not np.array_equal(result, test_image)
    print("✅ Single fragment test passed")
    
    # Test with multiple fragments
    fragments = [
        MockFragment([0, 0, 100, 100]),
        MockFragment([100, 0, 200, 100]),
        MockFragment([0, 100, 100, 200]),
        MockFragment([100, 100, 200, 200])
    ]
    result = draw_tile_boundaries(test_image, fragments)
    assert result.shape == test_image.shape
    print("✅ Multiple fragments test passed")
    
    # Test edge case: fragment at image boundary
    fragments = [MockFragment([0, 0, 300, 200])]  # Full image
    result = draw_tile_boundaries(test_image, fragments)
    assert result.shape == test_image.shape
    print("✅ Boundary fragment test passed")
    
    print("\n🎉 All tile boundary tests passed!")


if __name__ == "__main__":
    test_draw_tile_boundaries()