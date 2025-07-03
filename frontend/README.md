# Schemati Frontend

A simple Streamlit web application for uploading files to Databricks volumes.

## Features

- **Drag-and-drop file upload** - Simply drag files onto the upload area or click to browse
- **Image processing preview** - See both original and processed versions of images/PDFs before upload
- **Multiple file support** - Upload multiple files at once
- **Overwrite option** - Checkbox to control whether existing files should be overwritten
- **Real-time feedback** - Progress bar and status updates during upload
- **Volume contents view** - See what files are currently in the volume after upload
- **Configuration status** - Clear indication of Databricks connection status

## Usage

1. Ensure your Databricks configuration is set up (see Configuration section below)
2. Run the Streamlit app:
   ```bash
   uv run streamlit run frontend/app.py
   ```
3. Open your browser to the displayed URL (typically http://localhost:8501)
4. Use the interface to upload files:
   - Check/uncheck the "Overwrite existing files" option as needed
   - Drag files onto the upload area or click to select files
   - **Preview Tab**: View how your images/PDFs will be processed before uploading
     - See original vs. processed versions side-by-side
     - Check if files will be resized and by how much
     - Verify processing quality before proceeding
   - **Upload Tab**: Click "Upload Files" to start the upload process

## Configuration

The frontend uses the same configuration as the backend. You need to set up the following environment variables:

### Required
- `DATABRICKS_HOST` - Your Databricks workspace URL
- `DATABRICKS_CATALOG` - Target catalog name
- `DATABRICKS_SCHEMA` - Target schema name  
- `DATABRICKS_VOLUME` - Target volume name

### Authentication (choose one)
- **Token auth**: `DATABRICKS_TOKEN`
- **Service principal**: `DATABRICKS_CLIENT_ID` + `DATABRICKS_CLIENT_SECRET`
- **CLI auth**: Just `DATABRICKS_HOST` (uses Databricks CLI config)

### Example .env file
```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token-here
DATABRICKS_CATALOG=main
DATABRICKS_SCHEMA=default
DATABRICKS_VOLUME=uploads
```

## Technical Details

-The frontend is built using:
- **Streamlit** - Web framework for the user interface
- **VolumeFileStore** - Backend class for Databricks volume operations
- **Temporary files** - Files are temporarily stored during upload process
- **Error handling** - Comprehensive error handling and user feedback