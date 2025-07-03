"""Document parser for extracting data from P&ID pages using LLM."""

import base64
from typing import Dict, Any
from backend.documents.document import Page
from backend.llm.openai_client import OpenAIClient
from backend.llm.prompt_loader import load_prompt
from backend.logging import get_logger


class DocumentParser:
    """Parser for extracting structured data from document pages using LLM."""
    
    def __init__(self, openai_client: OpenAIClient) -> None:
        """Initialize the document parser.
        
        Args:
            openai_client: OpenAI client instance for LLM interactions
        """
        self.openai_client = openai_client
        self.logger = get_logger(__name__)
        
    def parse_page(self, page: Page) -> str:
        """Parse a page and extract structured data.
        
        Args:
            page: Page object to parse
            
        Returns:
            str: Parsed content/response from the LLM
        """
        self.logger.info(f"Parsing page {page.page_number}")
        
        # Load the extraction prompt
        try:
            system_prompt = load_prompt("extract_data")
        except FileNotFoundError:
            self.logger.error("extract_data.prompt not found")
            raise
        
        # Convert page content (bytes) to base64 for OpenAI Vision API
        if not page.content:
            self.logger.warning(f"Page {page.page_number} has no content")
            raise ValueError(f"Page {page.page_number} has no content to parse")
        
        # Encode image data as base64
        image_base64 = base64.b64encode(page.content).decode('utf-8')
        
        # Prepare messages for OpenAI Vision API
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text", 
                        "text": f"Please analyze this P&ID diagram (page {page.page_number}) and extract all the information according to the system prompt."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}",
                            "detail": "high"  # High detail for technical diagrams
                        }
                    }
                ]
            }
        ]
        
        # Send to LLM and get response
        try:
            response = self.openai_client.chat_completion(messages)
            self.logger.info(f"Successfully parsed page {page.page_number}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to parse page {page.page_number}: {e}")
            raise