from pathlib import Path
import tempfile
import cv2
import numpy as np

import pytest

from backend.documents.document import Document
from backend.documents.factory import DocumentFactory
from backend.config import set_config_for_test, get_config

ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.fixture
def factory() -> DocumentFactory:
    return DocumentFactory()


def test_create_document_from_image(factory: DocumentFactory):
    path = ASSETS_DIR / "test_image.jpg"
    doc = factory.from_disk(path)

    assert isinstance(doc, Document)
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert doc.pages[0].content is not None
    assert doc.path == path


def test_create_document_from_single_page_pdf(factory: DocumentFactory):
    path = ASSETS_DIR / "test_single_pg_pdf.pdf"
    doc = factory.from_disk(path)

    assert isinstance(doc, Document)
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert doc.pages[0].content is not None
    assert doc.path == path


def test_create_document_from_multi_page_pdf(factory: DocumentFactory):
    path = ASSETS_DIR / "test_multi_pg_pdf.pdf"
    doc = factory.from_disk(path)

    assert isinstance(doc, Document)
    assert len(doc.pages) > 1
    assert all(page.content is not None for page in doc.pages)
    assert [p.page_number for p in doc.pages] == list(range(1, len(doc.pages) + 1))
    assert doc.path == path


def test_unsupported_file_type_raises(factory: DocumentFactory):
    unsupported = ASSETS_DIR / "unsupported.txt"
    unsupported.write_text("Hello, I'm not a PDF or image")

    with pytest.raises(ValueError, match="Unsupported file type"):
        factory.from_disk(unsupported)

    unsupported.unlink()  # Clean up


def test_image_resize_functionality():
    """Test that images are resized when they exceed maximum dimensions."""
    # Create a test image that exceeds max dimensions
    large_image = np.zeros((3000, 4000, 3), dtype=np.uint8)  # 4000x3000 image
    
    # Set configuration for testing
    set_config_for_test(
        image_max_width=1024,
        image_max_height=768,
        image_dpi=150
    )
    
    try:
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, large_image)
            tmp_path = Path(tmp_file.name)
            
            try:
                factory = DocumentFactory()
                doc = factory.from_disk(tmp_path)
                
                # Verify document was created
                assert isinstance(doc, Document)
                assert len(doc.pages) == 1
                
                # Decode the image to check dimensions
                page_bytes = doc.pages[0].content
                nparr = np.frombuffer(page_bytes, np.uint8)
                decoded_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                height, width = decoded_image.shape[:2]
                
                # Image should be resized to fit within max dimensions
                assert width <= 1024
                assert height <= 768
                
                # Should maintain aspect ratio (original was 4000x3000 = 4:3)
                aspect_ratio = width / height
                original_aspect_ratio = 4000 / 3000
                assert abs(aspect_ratio - original_aspect_ratio) < 0.01
                
            finally:
                tmp_path.unlink()
    finally:
        # Reset config to defaults for other tests
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


def test_image_no_resize_when_within_limits():
    """Test that images are not resized when they're within the maximum dimensions."""
    # Create a small test image
    small_image = np.zeros((200, 300, 3), dtype=np.uint8)  # 300x200 image
    
    # Set configuration for testing
    set_config_for_test(
        image_max_width=1024,
        image_max_height=768,
        image_dpi=150
    )
    
    try:
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, small_image)
            tmp_path = Path(tmp_file.name)
            
            try:
                factory = DocumentFactory()
                doc = factory.from_disk(tmp_path)
                
                # Verify document was created
                assert isinstance(doc, Document)
                assert len(doc.pages) == 1
                
                # Decode the image to check dimensions
                page_bytes = doc.pages[0].content
                nparr = np.frombuffer(page_bytes, np.uint8)
                decoded_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                height, width = decoded_image.shape[:2]
                
                # Image should be approximately the same size (allowing for JPEG compression)
                assert 280 <= width <= 320  # Allow some variation due to JPEG compression
                assert 180 <= height <= 220
                
            finally:
                tmp_path.unlink()
    finally:
        # Reset config to defaults for other tests
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


def test_configurable_dpi_for_pdf():
    """Test that PDF conversion uses configurable DPI."""
    # Set configuration for testing
    set_config_for_test(
        image_dpi=150,  # Lower DPI for testing
        image_max_width=2048,
        image_max_height=2048
    )
    
    try:
        factory = DocumentFactory()
        path = ASSETS_DIR / "test_single_pg_pdf.pdf"
        doc = factory.from_disk(path)
        
        assert isinstance(doc, Document)
        assert len(doc.pages) == 1
        assert doc.pages[0].content is not None
        
        # Decode the image to verify it was processed
        page_bytes = doc.pages[0].content
        nparr = np.frombuffer(page_bytes, np.uint8)
        decoded_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Image should have been created (non-zero dimensions)
        height, width = decoded_image.shape[:2]
        assert width > 0
        assert height > 0
    finally:
        # Reset config to defaults for other tests
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


def test_pdf_image_resizing():
    """Test that PDF-derived images are resized when they exceed maximum dimensions."""
    # Set small max dimensions to force resizing
    set_config_for_test(
        image_dpi=300,  # High DPI to ensure large images
        image_max_width=400,
        image_max_height=400
    )
    
    try:
        factory = DocumentFactory()
        path = ASSETS_DIR / "test_single_pg_pdf.pdf"
        doc = factory.from_disk(path)
        
        assert isinstance(doc, Document)
        assert len(doc.pages) == 1
        
        # Decode the image to check dimensions
        page_bytes = doc.pages[0].content
        nparr = np.frombuffer(page_bytes, np.uint8)
        decoded_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        height, width = decoded_image.shape[:2]
        
        # Image should be resized to fit within max dimensions
        assert width <= 400
        assert height <= 400
    finally:
        # Reset config to defaults for other tests
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


def test_config_defaults():
    """Test that configuration defaults are sensible."""
    # Reset config to defaults before checking
    set_config_for_test(
        image_max_width=2048,
        image_max_height=2048,
        image_dpi=300
    )
    
    config = get_config()
    
    # Test that default values are reasonable
    assert config.image_dpi == 300
    assert config.image_max_width == 2048
    assert config.image_max_height == 2048
    assert config.image_dpi > 0
    assert config.image_max_width > 0
    assert config.image_max_height > 0


def test_preview_data_for_image():
    """Test that preview data is correctly generated for images."""
    # Create a large test image that should be resized
    large_image = np.zeros((3000, 4000, 3), dtype=np.uint8)
    
    # Set configuration for testing
    set_config_for_test(
        image_max_width=1024,
        image_max_height=768,
        image_dpi=150
    )
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, large_image)
            tmp_path = Path(tmp_file.name)
            
            try:
                factory = DocumentFactory()
                preview_data = factory.get_preview_data(tmp_path)
                
                # Should have one page of preview data
                assert len(preview_data) == 1
                
                page_data = preview_data[0]
                assert page_data['page_number'] == 1
                assert page_data['was_resized'] is True
                assert page_data['original_image'].shape == (3000, 4000, 3)
                assert page_data['processed_image'].shape[0] <= 768  # Height should be reduced
                assert page_data['processed_image'].shape[1] <= 1024  # Width should be reduced
                
            finally:
                tmp_path.unlink()
    finally:
        # Reset config to defaults
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


def test_preview_data_for_small_image():
    """Test that preview data correctly identifies when no resizing is needed."""
    # Create a small test image that should NOT be resized
    small_image = np.zeros((200, 300, 3), dtype=np.uint8)
    
    # Set configuration for testing
    set_config_for_test(
        image_max_width=1024,
        image_max_height=768,
        image_dpi=150
    )
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, small_image)
            tmp_path = Path(tmp_file.name)
            
            try:
                factory = DocumentFactory()
                preview_data = factory.get_preview_data(tmp_path)
                
                # Should have one page of preview data
                assert len(preview_data) == 1
                
                page_data = preview_data[0]
                assert page_data['page_number'] == 1
                assert page_data['was_resized'] is False
                # Images should be approximately the same (allowing for JPEG compression)
                assert abs(page_data['original_image'].shape[0] - page_data['processed_image'].shape[0]) <= 10
                assert abs(page_data['original_image'].shape[1] - page_data['processed_image'].shape[1]) <= 10
                
            finally:
                tmp_path.unlink()
    finally:
        # Reset config to defaults
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


def test_preview_data_for_pdf():
    """Test that preview data is correctly generated for PDF files."""
    set_config_for_test(
        image_dpi=300,
        image_max_width=400,
        image_max_height=400
    )
    
    try:
        factory = DocumentFactory()
        path = ASSETS_DIR / "test_single_pg_pdf.pdf"
        preview_data = factory.get_preview_data(path)
        
        # Should have one page of preview data
        assert len(preview_data) == 1
        
        page_data = preview_data[0]
        assert page_data['page_number'] == 1
        assert page_data['was_resized'] is True  # PDF should be resized given small max dimensions
        assert page_data['original_image'].shape[0] > 400 or page_data['original_image'].shape[1] > 400
        assert page_data['processed_image'].shape[0] <= 400
        assert page_data['processed_image'].shape[1] <= 400
        
    finally:
        # Reset config to defaults
        set_config_for_test(
            image_max_width=2048,
            image_max_height=2048,
            image_dpi=300
        )


def test_preview_data_unsupported_file():
    """Test that preview data raises appropriate error for unsupported files."""
    unsupported = ASSETS_DIR / "unsupported.txt"
    unsupported.write_text("Hello, I'm not a PDF or image")
    
    try:
        factory = DocumentFactory()
        with pytest.raises(ValueError, match="Unsupported file type"):
            factory.get_preview_data(unsupported)
    finally:
        unsupported.unlink()  # Clean up
