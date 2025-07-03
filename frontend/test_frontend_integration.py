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
    """Test that frontend can properly process files for preview using Document processing."""
    # Import the frontend preview functions
    from frontend.app import get_preview_data_for_image
    
    # Set test configuration
    set_config_for_test(
        image_max_width=1024,
        image_max_height=768,
        image_dpi=150
    )
    
    try:
        # Create a test image that should be resized (larger than limits)
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
        
        # For a large image, it should be resized by the Document processing
        assert page_data['was_resized'] == True, "Large image should be resized"
        
        # Check that processed image fits within limits (Document processing should resize it)
        processed_shape = page_data['processed_image'].shape
        assert processed_shape[0] <= 768, f"Processed height {processed_shape[0]} exceeds limit 768"
        assert processed_shape[1] <= 1024, f"Processed width {processed_shape[1]} exceeds limit 1024"
        
        # Original should be larger than processed
        original_shape = page_data['original_image'].shape
        assert original_shape[0] > processed_shape[0] or original_shape[1] > processed_shape[1], "Original should be larger than processed"
        
        print("✅ Frontend integration test passed!")
        print(f"   Original: {original_shape[1]}×{original_shape[0]}")
        print(f"   Processed: {processed_shape[1]}×{processed_shape[0]}")
        
    finally:
        # Reset config to defaults
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


if __name__ == "__main__":
    test_frontend_preview_integration()