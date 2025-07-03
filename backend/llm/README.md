# LLM Parsing Layer

This module provides a clean interface for parsing P&ID documents using OpenAI-compatible language models with support for vision capabilities.

## Configuration

Set the following environment variables or include them in your `.env` file:

```bash
# Required
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here

# Optional (with defaults)
OPENAI_MODEL=gpt-4o              # Model with vision capabilities
OPENAI_TEMPERATURE=0.1           # Low temperature for consistent extraction
OPENAI_MAX_TOKENS=4000          # Maximum response tokens
```

## Basic Usage

```python
from backend.llm.openai_client import OpenAIClient
from backend.llm.document_parser import DocumentParser
from backend.documents.document import Page

# Initialize the OpenAI client
client = OpenAIClient()

# Create a document parser
parser = DocumentParser(client)

# Parse a page with image data
page = Page(page_number=1, content=image_bytes)
result = parser.parse_page(page)

print(result)  # JSON response with extracted P&ID data
```

## Components

### OpenAIClient

Wrapper around OpenAI ChatCompletion API with:
- Configuration management for model, temperature, and token limits
- Vision API support for image analysis
- Comprehensive error handling

### DocumentParser

Main parsing class that:
- Processes image data from Page objects
- Combines system prompts with image content
- Handles base64 encoding for OpenAI Vision API
- Validates page content before processing

### load_prompt()

Utility function to load prompts from the `backend/llm/prompts/` directory.

## Image Processing

The DocumentParser now supports actual image data processing:
- Accepts binary image data from Page.content
- Automatically encodes images as base64 for OpenAI Vision API
- Uses high-detail image analysis for technical diagrams
- Validates that pages contain actual content before processing

## Prompts

Prompts are stored in `backend/llm/prompts/` with the `.prompt` extension. The `extract_data.prompt` file contains detailed instructions for P&ID parsing with a comprehensive JSON schema.

## Testing

Run tests with:

```bash
PYTHONPATH=. python -m pytest backend/tests/test_llm.py -v
```

## Future Enhancements

- Add support for different model providers
- Implement prompt templating with Jinja2
- Add OCR support for image-based documents
- Support for multi-page document-level reasoning