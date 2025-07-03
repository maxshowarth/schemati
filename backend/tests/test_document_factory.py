import pytest
from pathlib import Path
from backend.routers.factories.document_factory import DocumentFactory
from backend.models.document import Document

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
    assert doc.pages[0].bytes is not None
    assert doc.path == path

def test_create_document_from_single_page_pdf(factory: DocumentFactory):
    path = ASSETS_DIR / "test_single_pg_pdf.pdf"
    doc = factory.from_disk(path)

    assert isinstance(doc, Document)
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert doc.pages[0].bytes is not None
    assert doc.path == path

def test_create_document_from_multi_page_pdf(factory: DocumentFactory):
    path = ASSETS_DIR / "test_multi_pg_pdf.pdf"
    doc = factory.from_disk(path)

    assert isinstance(doc, Document)
    assert len(doc.pages) > 1
    assert all(page.bytes is not None for page in doc.pages)
    assert [p.page_number for p in doc.pages] == list(range(1, len(doc.pages) + 1))
    assert doc.path == path

def test_unsupported_file_type_raises(factory: DocumentFactory):
    unsupported = ASSETS_DIR / "unsupported.txt"
    unsupported.write_text("Hello, I'm not a PDF or image")

    with pytest.raises(ValueError, match="Unsupported file type"):
        factory.from_disk(unsupported)

    unsupported.unlink()  # Clean up
