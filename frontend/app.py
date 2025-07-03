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

# Add the parent directory to sys.path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.databricks.volume import create_volume_file_store_from_config
from backend.logging import get_logger
from backend.exceptions import FileAlreadyExistsError, FileNotFoundError, VolumeUploadError
from backend.documents.factory import DocumentFactory

logger = get_logger(__name__)

st.set_page_config(
    page_title="Schemati File Uploader",
    page_icon="📁",
    layout="wide"
)

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
                    # Save uploaded file temporarily for preview
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = Path(tmp_file.name)
                        
                        # Get preview data using DocumentFactory
                        factory = DocumentFactory()
                        file_preview = factory.get_preview_data(tmp_file_path)
                        preview_data[uploaded_file.name] = file_preview
                        
                        # Clean up temporary file
                        os.unlink(tmp_file.name)
                        
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
    
    if total_pages > 1:  # Multi-page document
        st.markdown(f"**Page {page_num}:**")
    
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
            # Convert from BGR to RGB for display
            processed_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            st.image(processed_rgb, use_container_width=True)
            st.caption(f"Size: {processed.shape[1]}×{processed.shape[0]}")
    else:
        st.success(f"✅ This {'page' if total_pages > 1 else 'image'} is within size limits and will not be resized.")
        
        # Show just the original image
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        st.image(original_rgb, use_container_width=True)
        st.caption(f"Size: {original.shape[1]}×{original.shape[0]}")

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