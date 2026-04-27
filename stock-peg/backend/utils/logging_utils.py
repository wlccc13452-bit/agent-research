"""
Logging Utilities - Secure logging with sensitive data masking

Provides utilities for safe logging that prevents sensitive information leakage.
"""

import re
from typing import Any, Dict, List
from config.constants import LoggingConfig


def mask_sensitive_data(data: Any, mask: str = "***") -> Any:
    """
    Recursively mask sensitive data in dictionaries and lists
    
    Args:
        data: Data to mask (dict, list, or other)
        mask: Mask string to replace sensitive values
    
    Returns:
        Data with sensitive values masked
    """
    if isinstance(data, dict):
        return {
            key: mask if _is_sensitive_field(key) else mask_sensitive_data(value, mask)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, mask) for item in data]
    else:
        return data


def _is_sensitive_field(field_name: str) -> bool:
    """
    Check if field name is sensitive
    
    Args:
        field_name: Field name to check
    
    Returns:
        True if field is sensitive
    """
    field_lower = field_name.lower()
    return any(sensitive in field_lower for sensitive in LoggingConfig.SENSITIVE_FIELD_NAMES)


def truncate_for_logging(text: str, max_length: int = LoggingConfig.MAX_CONTENT_PREVIEW_LENGTH) -> str:
    """
    Truncate text for logging purposes
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def safe_log_message_id(message_id: str) -> str:
    """
    Safely log message ID (truncated)
    
    Args:
        message_id: Full message ID
    
    Returns:
        Truncated message ID for logging
    """
    if not message_id:
        return "<empty>"
    return message_id[:LoggingConfig.MAX_MESSAGE_ID_DISPLAY_LENGTH]


def sanitize_card_content(card_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize card content for safe logging
    
    Removes or masks potentially sensitive information from card content
    before logging.
    
    Args:
        card_content: Card content dictionary
    
    Returns:
        Sanitized card content safe for logging
    """
    # Create a copy to avoid modifying original
    sanitized = mask_sensitive_data(card_content)
    
    # Truncate long text content
    if "elements" in sanitized and isinstance(sanitized["elements"], list):
        for element in sanitized["elements"]:
            if isinstance(element, dict) and "text" in element:
                text_obj = element["text"]
                if isinstance(text_obj, dict) and "content" in text_obj:
                    text_obj["content"] = truncate_for_logging(
                        str(text_obj["content"]),
                        LoggingConfig.MAX_CONTENT_PREVIEW_LENGTH
                    )
    
    return sanitized


def log_api_call(api_name: str, params: Dict[str, Any], result: str = "success") -> str:
    """
    Format API call for logging with masked sensitive data
    
    Args:
        api_name: API endpoint name
        params: API parameters
        result: Call result
    
    Returns:
        Formatted log message
    """
    masked_params = mask_sensitive_data(params)
    return f"API {api_name}: {masked_params} -> {result}"


# Example usage
if __name__ == "__main__":
    # Test masking
    test_data = {
        "username": "user123",
        "password": "secret123",
        "api_key": "abc123xyz",
        "data": {
            "token": "bearer_token_here",
            "content": "Some long content that should be truncated for logging purposes..."
        }
    }
    
    print("Original:", test_data)
    print("Masked:", mask_sensitive_data(test_data))
    print("Sanitized card:", sanitize_card_content(test_data))
