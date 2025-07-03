"""
Basic tests for the frontend app functionality.
"""
import sys
import tempfile
from pathlib import Path
import cv2
import numpy as np

# Add the parent directory to sys.path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.documents.factory import DocumentFactory


def test_frontend_preview_integration():
    """Test that frontend can properly use the DocumentFactory preview functionality."""
    factory = DocumentFactory()
    
    # Create a test image
    test_image = np.zeros((1000, 1500, 3), dtype=np.uint8)
    test_image[:, :, 0] = 255  # Red image
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        cv2.imwrite(tmp_file.name, test_image)
        tmp_path = Path(tmp_file.name)
        
        try:
            # Test that we can get preview data
            preview_data = factory.get_preview_data(tmp_path)
            
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
            
            print("✅ Frontend integration test passed!")
            
        finally:
            tmp_path.unlink()


if __name__ == "__main__":
    test_frontend_preview_integration()