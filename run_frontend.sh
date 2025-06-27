#!/usr/bin/env bash
"""
Startup script for the Schemati frontend.

This script starts the Streamlit application with appropriate configuration.
"""

cd "$(dirname "$0")"
exec uv run streamlit run frontend/app.py --server.headless false --server.port 8501