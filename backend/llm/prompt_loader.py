"""Utility functions for loading prompts."""

from pathlib import Path
from backend.logging import get_logger

logger = get_logger(__name__)


def load_prompt(prompt_name: str) -> str:
    """Load a prompt from the prompts directory.
    
    Args:
        prompt_name: Name of the prompt file (without .prompt extension)
        
    Returns:
        str: The loaded prompt content
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        RuntimeError: If there's an error reading the file
    """
    # Get the directory where this file is located
    current_dir = Path(__file__).parent
    prompt_path = current_dir / "prompts" / f"{prompt_name}.prompt"
    
    logger.debug(f"Loading prompt from: {prompt_path}")
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Successfully loaded prompt '{prompt_name}' ({len(content)} characters)")
        return content
    except Exception as e:
        logger.error(f"Error reading prompt file {prompt_path}: {e}")
        raise RuntimeError(f"Error reading prompt file {prompt_path}: {e}")