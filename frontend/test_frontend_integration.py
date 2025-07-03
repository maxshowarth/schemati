"""
Basic tests for the frontend app functionality.
"""
import sys
import tempfile
from pathlib import Path
import cv2
import numpy as np
from unittest.mock import Mock

# Add the parent directory to sys.path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import set_config_for_test


def test_frontend_preview_integration():
    """Test that frontend can properly process files for preview without backend dependency."""
    # Import the frontend preview functions
    from frontend.app import get_preview_data_for_image, resize_image_if_needed
    
    # Set test configuration
    set_config_for_test(
        image_max_width=1024,
        image_max_height=768,
        image_dpi=150
    )
    
    try:
        # Create a test image
        test_image = np.zeros((1000, 1500, 3), dtype=np.uint8)
        test_image[:, :, 0] = 255  # Red image
        
        # Encode to bytes (simulating uploaded file)
        _, img_bytes = cv2.imencode('.jpg', test_image)
        img_bytes = img_bytes.tobytes()
        
        # Test image preview functionality
        preview_data = get_preview_data_for_image(img_bytes, "test_image.jpg")
        
        # Verify the structure expected by the frontend
        assert len(preview_data) == 1
        page_data = preview_data[0]
        
        # Check all required keys exist
        required_keys = ['page_number', 'original_image', 'processed_image', 'was_resized']
        for key in required_keys:
            assert key in page_data, f"Missing required key: {key}"
        
        # Check that images are numpy arrays (as expected by frontend)
        assert isinstance(page_data['original_image'], np.ndarray)
        assert isinstance(page_data['processed_image'], np.ndarray)
        
        # Check that images have proper shape for display
        assert len(page_data['original_image'].shape) == 3
        assert len(page_data['processed_image'].shape) == 3
        
        # Check that page number is correct
        assert page_data['page_number'] == 1
        
        # Check that was_resized is boolean
        assert isinstance(page_data['was_resized'], bool)
        
        # Test resize functionality
        large_image = np.zeros((2000, 3000, 3), dtype=np.uint8)
        resized_image = resize_image_if_needed(large_image)
        
        # Should be resized to fit within limits
        assert resized_image.shape[0] <= 768  # Height
        assert resized_image.shape[1] <= 1024  # Width
        
        print("✅ Frontend integration test passed!")
        
    finally:
        # Reset config to defaults
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


if __name__ == "__main__":
    test_frontend_preview_integration()