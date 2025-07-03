# LLM Parsing Layer

This module provides a clean interface for parsing P&ID documents using OpenAI-compatible language models.

## Configuration

Set the following environment variables or include them in your `.env` file:

```bash
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here
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

# Parse a page
page = Page(page_number=1, content=b"page content")
result = parser.parse_page(page)

print(result)  # JSON response with extracted P&ID data
```

## Components

### OpenAIClient

Wrapper around OpenAI ChatCompletion API with error handling and configuration management.

### DocumentParser

Main parsing class that combines prompts with page content for LLM processing.

### load_prompt()

Utility function to load prompts from the `backend/llm/prompts/` directory.

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