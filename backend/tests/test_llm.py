"""Tests for LLM functionality."""

import pytest
from unittest.mock import Mock, patch, mock_open
from backend.llm.openai_client import OpenAIClient
from backend.llm.prompt_loader import load_prompt
from backend.llm.document_parser import DocumentParser
from backend.documents.document import Page
from backend.config import set_config_for_test


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Clear environment variables before each test."""
    for var in [
        "OPENAI_BASE_URL", "OPENAI_API_KEY"
    ]:
        monkeypatch.delenv(var, raising=False)


class TestOpenAIClient:
    """Test cases for OpenAIClient."""
    
    def test_init_with_config(self):
        """Test OpenAIClient initialization with valid config."""
        set_config_for_test(
            openai_base_url="https://api.openai.com/v1",
            openai_api_key="test-key",
            openai_model="gpt-4o",
            openai_temperature=0.2,
            openai_max_tokens=5000
        )
        client = OpenAIClient()
        assert client.base_url == "https://api.openai.com/v1"
        assert client.api_key == "test-key"
    
    def test_init_missing_base_url(self):
        """Test OpenAIClient initialization fails without base URL."""
        set_config_for_test(
            openai_base_url=None,
            openai_api_key="test-key"
        )
        with pytest.raises(ValueError, match="OpenAI base URL is required"):
            OpenAIClient()
    
    def test_init_missing_api_key(self):
        """Test OpenAIClient initialization fails without API key."""
        set_config_for_test(
            openai_base_url="https://api.openai.com/v1",
            openai_api_key=None
        )
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            OpenAIClient()
    
    @patch('backend.llm.openai_client.requests.post')
    def test_chat_completion_success(self, mock_post):
        """Test successful chat completion."""
        # Setup
        set_config_for_test(
            openai_base_url="https://api.openai.com/v1",
            openai_api_key="test-key",
            openai_model="gpt-4o",
            openai_temperature=0.2,
            openai_max_tokens=5000
        )
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        
        client = OpenAIClient()
        messages = [{"role": "user", "content": "Test message"}]
        
        # Test
        result = client.chat_completion(messages)
        
        # Verify
        assert result == "Test response"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["messages"] == messages
        assert call_args[1]["json"]["model"] == "gpt-4o"
        assert call_args[1]["json"]["temperature"] == 0.2
        assert call_args[1]["json"]["max_tokens"] == 5000
    
    @patch('backend.llm.openai_client.requests.post')
    def test_chat_completion_request_error(self, mock_post):
        """Test chat completion with request error."""
        # Setup
        set_config_for_test(
            openai_base_url="https://api.openai.com/v1",
            openai_api_key="test-key"
        )
        
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        client = OpenAIClient()
        messages = [{"role": "user", "content": "Test message"}]
        
        # Test
        with pytest.raises(RuntimeError, match="OpenAI API request failed"):
            client.chat_completion(messages)


class TestPromptLoader:
    """Test cases for prompt loading functionality."""
    
    def test_load_prompt_success(self):
        """Test successful prompt loading."""
        # Test with a real prompt file that exists
        result = load_prompt("extract_data")
        
        # Verify the file content is loaded
        assert "You are a highly accurate and detail-oriented engineering assistant" in result
        assert "P&ID" in result
    
    def test_load_prompt_file_not_found(self):
        """Test prompt loading when file doesn't exist."""
        # Test with a non-existent prompt file
        with pytest.raises(FileNotFoundError, match="Prompt file not found"):
            load_prompt("nonexistent_prompt")
    
    @patch('builtins.open', new_callable=mock_open)
    def test_load_prompt_read_error(self, mock_file):
        """Test prompt loading with read error."""
        # Setup the mock to raise an exception when reading
        mock_file.return_value.read.side_effect = Exception("Read error")
        
        # Test with a known prompt file that exists
        with pytest.raises(RuntimeError, match="Error reading prompt file"):
            load_prompt("extract_data")


class TestDocumentParser:
    """Test cases for DocumentParser."""
    
    def test_init(self):
        """Test DocumentParser initialization."""
        mock_client = Mock(spec=OpenAIClient)
        parser = DocumentParser(mock_client)
        assert parser.openai_client == mock_client
    
    @patch('backend.llm.document_parser.load_prompt')
    def test_parse_page_success(self, mock_load_prompt):
        """Test successful page parsing."""
        # Setup
        mock_client = Mock(spec=OpenAIClient)
        mock_client.chat_completion.return_value = "Parsed content"
        mock_load_prompt.return_value = "System prompt"
        
        parser = DocumentParser(mock_client)
        # Create page with sample image content (fake PNG bytes)
        page = Page(page_number=1, content=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82')
        
        # Test
        result = parser.parse_page(page)
        
        # Verify
        assert result == "Parsed content"
        mock_load_prompt.assert_called_once_with("extract_data")
        mock_client.chat_completion.assert_called_once()
        
        # Check the messages passed to chat_completion
        call_args = mock_client.chat_completion.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["role"] == "system"
        assert call_args[0]["content"] == "System prompt"
        assert call_args[1]["role"] == "user"
        assert "content" in call_args[1]
        assert isinstance(call_args[1]["content"], list)
        assert len(call_args[1]["content"]) == 2
        # Check text content
        assert call_args[1]["content"][0]["type"] == "text"
        assert "page 1" in call_args[1]["content"][0]["text"]
        # Check image content
        assert call_args[1]["content"][1]["type"] == "image_url"
        assert "data:image/png;base64," in call_args[1]["content"][1]["image_url"]["url"]
    
    @patch('backend.llm.document_parser.load_prompt')
    def test_parse_page_prompt_not_found(self, mock_load_prompt):
        """Test page parsing when prompt file is not found."""
        # Setup
        mock_client = Mock(spec=OpenAIClient)
        mock_load_prompt.side_effect = FileNotFoundError("Prompt not found")
        
        parser = DocumentParser(mock_client)
        page = Page(page_number=1, content=b"test content")
        
        # Test
        with pytest.raises(FileNotFoundError):
            parser.parse_page(page)
    
    @patch('backend.llm.document_parser.load_prompt')
    def test_parse_page_empty_content(self, mock_load_prompt):
        """Test page parsing with empty content."""
        # Setup
        mock_client = Mock(spec=OpenAIClient)
        mock_load_prompt.return_value = "System prompt"
        
        parser = DocumentParser(mock_client)
        page = Page(page_number=1, content=b"")  # Empty content
        
        # Test
        with pytest.raises(ValueError, match="Page 1 has no content to parse"):
            parser.parse_page(page)
    
    @patch('backend.llm.document_parser.load_prompt')
    def test_parse_page_llm_error(self, mock_load_prompt):
        """Test page parsing when LLM call fails."""
        # Setup
        mock_client = Mock(spec=OpenAIClient)
        mock_client.chat_completion.side_effect = Exception("LLM error")
        mock_load_prompt.return_value = "System prompt"
        
        parser = DocumentParser(mock_client)
        page = Page(page_number=1, content=b"test content")
        
        # Test
        with pytest.raises(Exception, match="LLM error"):
            parser.parse_page(page)