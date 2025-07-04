"""
Streamlit frontend for uploading files to Databricks volumes.

This application provides a simple drag-and-drop interface for uploading files
to Databricks volumes using the Volume and VolumeFileStore classes from the backend.
"""

import streamlit as st
import tempfile
import os
import sys
from pathlib import Path
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF

# Add the parent directory to sys.path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.databricks.volume import create_volume_file_store_from_config
from backend.logging import get_logger
from backend.exceptions import FileAlreadyExistsError, FileNotFoundError, VolumeUploadError
from backend.documents.factory import DocumentFactory
from backend.config import get_config

logger = get_logger(__name__)

def draw_tile_boundaries(image: np.ndarray, fragments: list) -> np.ndarray:
    """Draw tile boundaries on an image.
    
    Args:
        image: The input image (BGR format)
        fragments: List of PageFragment objects with bbox attributes
        
    Returns:
        Image with red rectangle boundaries drawn
    """
    # Make a copy to avoid modifying the original
    image_with_boundaries = image.copy()
    
    # Draw rectangles for each fragment
    for fragment in fragments:
        x1, y1, x2, y2 = fragment.bbox
        # Draw rectangle border (red color in BGR format, thickness 2)
        cv2.rectangle(image_with_boundaries, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    return image_with_boundaries

st.set_page_config(
    page_title="Schemati File Uploader",
    page_icon="📁",
    layout="wide"
)

def get_preview_data_for_image(file_bytes: bytes, filename: str) -> list[dict]:
    """Get preview data for a single image file using native loaders and Document processing."""
    # Load original image using PIL (native frontend loader)
    try:
        original_pil = Image.open(BytesIO(file_bytes))
        original_array = np.array(original_pil)
        # Convert RGB to BGR for OpenCV compatibility in display
        if len(original_array.shape) == 3 and original_array.shape[2] == 3:
            original_image = cv2.cvtColor(original_array, cv2.COLOR_RGB2BGR)
        else:
            original_image = original_array
    except Exception as e:
        raise ValueError(f"Failed to load original image {filename}: {e}")
    
    # Create Document using DocumentFactory to get processed content
    try:
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file_path = tmp_file.name
            
        try:
            factory = DocumentFactory()
            document = factory.from_disk(Path(tmp_file_path))
            
            # Extract processed image from Document.pages[0].content
            page_content = document.pages[0].content
            processed_array = np.frombuffer(page_content, np.uint8)
            processed_image = cv2.imdecode(processed_array, cv2.IMREAD_COLOR)
            
            if processed_image is None:
                raise ValueError("Failed to decode processed image from Document")
            
            # Fragment the page to get tile boundaries
            fragments = document.pages[0].fragment(complexity_threshold=0.0)
            
            # Check if resizing occurred by comparing dimensions
            was_resized = (original_image.shape[:2] != processed_image.shape[:2])
            
            return [{
                'page_number': 1,
                'original_image': original_image,
                'processed_image': processed_image,
                'was_resized': was_resized,
                'fragments': fragments
            }]
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except Exception as e:
        raise RuntimeError(f"Failed to create Document for {filename}: {e}")

def get_preview_data_for_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    """Get preview data for a PDF file using native loaders and Document processing."""
    app_config = get_config()
    preview_data = []
    
    try:
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_file_path = tmp_file.name
            
        try:
            # Load original PDF using PyMuPDF (native frontend loader)
            original_doc = fitz.open(tmp_file_path)
            
            # Create Document using DocumentFactory to get processed content
            factory = DocumentFactory()
            document = factory.from_disk(Path(tmp_file_path))
            
            # Process each page
            for i, (original_page, document_page) in enumerate(zip(original_doc, document.pages)):
                # Get original page as image using native loader
                pix = original_page.get_pixmap(dpi=app_config.image_dpi)
                original_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if original_array.shape[2] == 4:
                    original_array = cv2.cvtColor(original_array, cv2.COLOR_RGBA2RGB)
                # Convert RGB to BGR for OpenCV compatibility
                original_image = cv2.cvtColor(original_array, cv2.COLOR_RGB2BGR)
                
                # Extract processed image from Document.pages[i].content
                page_content = document_page.content
                processed_array = np.frombuffer(page_content, np.uint8)
                processed_image = cv2.imdecode(processed_array, cv2.IMREAD_COLOR)
                
                if processed_image is None:
                    raise ValueError(f"Failed to decode processed page {i+1} from Document")
                
                # Fragment the page to get tile boundaries
                fragments = document_page.fragment(complexity_threshold=0.0)
                
                # Check if resizing occurred by comparing dimensions
                was_resized = (original_image.shape[:2] != processed_image.shape[:2])
                
                preview_data.append({
                    'page_number': i + 1,
                    'original_image': original_image,
                    'processed_image': processed_image,
                    'was_resized': was_resized,
                    'fragments': fragments
                })
            
            return preview_data
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
    except Exception as e:
        raise RuntimeError(f"Failed to preview PDF {filename}: {e}")

def get_preview_data(uploaded_file) -> list[dict]:
    """Get preview data for any supported file type."""
    app_config = get_config()
    file_extension = Path(uploaded_file.name).suffix.lower()
    file_bytes = uploaded_file.getvalue()
    
    if file_extension in app_config.allowed_image_extensions:
        return get_preview_data_for_image(file_bytes, uploaded_file.name)
    elif file_extension in app_config.allowed_pdf_extensions:
        return get_preview_data_for_pdf(file_bytes, uploaded_file.name)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def main():
    """Main Streamlit application."""
    st.title("📁 Schemati File Uploader")
    st.markdown("Upload files to Databricks volumes with ease!")
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Get current configuration status
    try:
        file_store = create_volume_file_store_from_config()
        config_status = "✅ Connected"
        config_details = f"Catalog: {file_store.volume.catalog}\nSchema: {file_store.volume.schema_name}\nVolume: {file_store.volume.volume_name}"
    except Exception as e:
        config_status = "❌ Configuration Error"
        config_details = str(e)
        file_store = None
    
    st.sidebar.markdown(f"**Status:** {config_status}")
    st.sidebar.text(config_details)
    
    if file_store is None:
        st.error("⚠️ **Configuration Error**")
        st.markdown("""
        Unable to connect to Databricks. Please ensure your environment is configured with:
        - `DATABRICKS_HOST`
        - `DATABRICKS_TOKEN` or `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET`
        - `DATABRICKS_CATALOG`
        - `DATABRICKS_SCHEMA` 
        - `DATABRICKS_VOLUME`
        
        See the `.env.template` file for reference.
        """)
        return
    
    # Show volume contents on page load
    show_volume_contents(file_store)
    
    # Main upload interface
    st.header("File Upload")
    
    # Overwrite checkbox
    overwrite = st.checkbox(
        "Overwrite existing files",
        value=False,
        help="If checked, files with the same name will be overwritten. Otherwise, upload will fail if file already exists."
    )
    
    # File uploader with drag and drop
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        help="Drag and drop files here or click to browse"
    )
    
    if uploaded_files:
        st.subheader("File Preview")
        
        # Create tabs for preview and upload
        preview_tab, upload_tab = st.tabs(["📋 Preview Processing", "🚀 Upload Files"])
        
        with preview_tab:
            st.markdown("**Preview how your files will be processed before uploading:**")
            
            # Process each file for preview
            preview_data = {}
            for uploaded_file in uploaded_files:
                try:
                    # Get preview data directly from uploaded file
                    file_preview = get_preview_data(uploaded_file)
                    preview_data[uploaded_file.name] = file_preview
                        
                except Exception as e:
                    st.error(f"❌ Failed to preview {uploaded_file.name}: {str(e)}")
                    continue
            
            # Display preview for each file
            for filename, pages in preview_data.items():
                with st.expander(f"📄 {filename} - {len(pages)} page(s)"):
                    for page_data in pages:
                        show_image_comparison(page_data, filename, len(pages))
        
        with upload_tab:
            st.subheader("Selected Files")
            
            # Display file information
            for file in uploaded_files:
                with st.expander(f"📄 {file.name} ({file.size:,} bytes)"):
                    st.write(f"**Name:** {file.name}")
                    st.write(f"**Size:** {file.size:,} bytes")
                    st.write(f"**Type:** {file.type}")
            
            # Upload button
            if st.button("🚀 Upload Files", type="primary"):
                upload_files(uploaded_files, file_store, overwrite)

def show_image_comparison(page_data, filename, total_pages):
    """Display side-by-side comparison of original vs processed image."""
    page_num = page_data['page_number']
    original = page_data['original_image']
    processed = page_data['processed_image']
    was_resized = page_data['was_resized']
    fragments = page_data.get('fragments', [])
    
    if total_pages > 1:  # Multi-page document
        st.markdown(f"**Page {page_num}:**")
    
    # Add checkbox to toggle tile boundaries
    show_boundaries = st.checkbox(
        f"🔲 Show tile boundaries {'for page ' + str(page_num) if total_pages > 1 else ''}",
        value=False,
        key=f"boundaries_{filename}_{page_num}",
        help="Display red rectangles showing how the image will be divided into tiles for processing"
    )
    
    if was_resized:
        st.info(f"🔄 This {'page' if total_pages > 1 else 'image'} will be resized during processing.")
        
        # Create two columns for side-by-side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original:**")
            # Convert from BGR to RGB for display
            original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
            st.image(original_rgb, use_container_width=True)
            st.caption(f"Size: {original.shape[1]}×{original.shape[0]}")
        
        with col2:
            st.markdown("**After Processing:**")
            # Get processed image to display
            display_image = processed
            if show_boundaries and fragments:
                display_image = draw_tile_boundaries(processed, fragments)
            
            # Convert from BGR to RGB for display
            processed_rgb = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
            st.image(processed_rgb, use_container_width=True)
            caption = f"Size: {processed.shape[1]}×{processed.shape[0]}"
            if show_boundaries and fragments:
                caption += f" | {len(fragments)} tiles"
            st.caption(caption)
    else:
        st.success(f"✅ This {'page' if total_pages > 1 else 'image'} is within size limits and will not be resized.")
        
        # Show the original image (which is same as processed)
        display_image = original
        if show_boundaries and fragments:
            display_image = draw_tile_boundaries(original, fragments)
            
        display_rgb = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        st.image(display_rgb, use_container_width=True)
        caption = f"Size: {original.shape[1]}×{original.shape[0]}"
        if show_boundaries and fragments:
            caption += f" | {len(fragments)} tiles"
        st.caption(caption)

def upload_files(uploaded_files, file_store, overwrite):
    """Upload files to Databricks volume."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(uploaded_files)
    successful_uploads = 0
    failed_uploads = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Uploading {uploaded_file.name}...")
        progress_bar.progress((i + 1) / total_files)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            try:
                # Write uploaded file content to temporary file
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
                
                # Upload using VolumeFileStore with original filename
                success = file_store.upload_file(tmp_file_path, overwrite=overwrite, destination_filename=uploaded_file.name)
                
                if success:
                    successful_uploads += 1
                    logger.info(f"Successfully uploaded {uploaded_file.name}")
                    
            except FileAlreadyExistsError as e:
                failed_uploads.append({
                    'filename': uploaded_file.name,
                    'error': f"File already exists in volume '{e.volume_name}'. Enable 'Overwrite existing files' to replace it."
                })
                logger.error(f"File already exists: {uploaded_file.name}")
                
            except FileNotFoundError as e:
                failed_uploads.append({
                    'filename': uploaded_file.name,
                    'error': f"Temporary file could not be created or accessed."
                })
                logger.error(f"File not found: {e}")
                
            except VolumeUploadError as e:
                failed_uploads.append({
                    'filename': uploaded_file.name,
                    'error': f"Upload failed: {e.original_error}"
                })
                logger.error(f"Upload error: {e}")
                
            except Exception as e:
                failed_uploads.append({
                    'filename': uploaded_file.name,
                    'error': f"Unexpected error: {str(e)}"
                })
                logger.error(f"Unexpected error uploading {uploaded_file.name}: {e}")
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {tmp_file_path}: {e}")
    
    # Display results
    status_text.empty()
    progress_bar.empty()
    
    if successful_uploads > 0:
        st.success(f"✅ Successfully uploaded {successful_uploads} file(s)!")
    
    if failed_uploads:
        st.error(f"❌ Failed to upload {len(failed_uploads)} file(s):")
        for failed_upload in failed_uploads:
            st.write(f"**{failed_upload['filename']}**: {failed_upload['error']}")
    
    # Show volume contents
    if successful_uploads > 0:
        show_volume_contents(file_store)

def show_volume_contents(file_store):
    """Display current files in the volume."""
    st.subheader("📂 Volume Contents")
    
    try:
        files = file_store.list_files()
        if files:
            st.write(f"Found {len(files)} file(s) in the volume:")
            for file_path in files:
                filename = os.path.basename(file_path)
                st.write(f"- {filename}")
        else:
            st.info("No files found in the volume.")
    except Exception as e:
        st.error(f"Failed to list volume contents: {e}")

if __name__ == "__main__":
    main()