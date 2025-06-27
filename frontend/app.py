"""
Streamlit frontend for uploading files to Databricks volumes.

This application provides a simple drag-and-drop interface for uploading files
to Databricks volumes using the VolumeHandler class from the backend.
"""

import streamlit as st
import tempfile
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.routers.volume import VolumeHandler
from backend.logging import get_logger

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
        volume_handler = VolumeHandler()
        config_status = "✅ Connected"
        config_details = f"Catalog: {volume_handler.catalog}\nSchema: {volume_handler.schema}\nVolume: {volume_handler.volume_name}"
    except Exception as e:
        config_status = "❌ Configuration Error"
        config_details = str(e)
        volume_handler = None
    
    st.sidebar.markdown(f"**Status:** {config_status}")
    st.sidebar.text(config_details)
    
    if volume_handler is None:
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
        st.subheader("Selected Files")
        
        # Display file information
        for file in uploaded_files:
            with st.expander(f"📄 {file.name} ({file.size:,} bytes)"):
                st.write(f"**Name:** {file.name}")
                st.write(f"**Size:** {file.size:,} bytes")
                st.write(f"**Type:** {file.type}")
        
        # Upload button
        if st.button("🚀 Upload Files", type="primary"):
            upload_files(uploaded_files, volume_handler, overwrite)

def upload_files(uploaded_files, volume_handler, overwrite):
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
                
                # Upload using VolumeHandler
                success = volume_handler.upload_file(tmp_file_path, overwrite=overwrite)
                
                if success:
                    successful_uploads += 1
                    logger.info(f"Successfully uploaded {uploaded_file.name}")
                else:
                    failed_uploads.append(uploaded_file.name)
                    logger.error(f"Failed to upload {uploaded_file.name}")
                    
            except Exception as e:
                failed_uploads.append(uploaded_file.name)
                logger.error(f"Error uploading {uploaded_file.name}: {e}")
                
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
        for filename in failed_uploads:
            st.write(f"- {filename}")
    
    # Show volume contents
    if successful_uploads > 0:
        show_volume_contents(volume_handler)

def show_volume_contents(volume_handler):
    """Display current files in the volume."""
    st.subheader("📂 Volume Contents")
    
    try:
        files = volume_handler.list_files()
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