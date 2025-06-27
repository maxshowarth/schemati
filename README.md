# schemati
Extract critical information from P&ID diagrams and other similar schematics using ML on Databricks

## Components

### Backend
Contains the core functionality for interacting with Databricks volumes, including:
- `VolumeHandler` class for file operations
- Authentication and configuration management
- Logging utilities

### Frontend
A Streamlit web application for uploading files to Databricks volumes:
- Drag-and-drop file upload interface
- Overwrite option control
- Real-time upload progress and feedback

## Quick Start

### Running the Frontend
```bash
# Install dependencies
uv sync

# Run the Streamlit app
uv run streamlit run frontend/app.py
```

### Configuration
Set up your environment variables in a `.env` file (see `.env.template` for reference).
