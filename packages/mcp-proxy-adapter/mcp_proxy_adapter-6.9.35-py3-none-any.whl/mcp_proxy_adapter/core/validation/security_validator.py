"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Security validation utilities for MCP Proxy Adapter configuration validation.
"""

import os
from typing import Dict, List, Any

from .validation_result import ValidationResult


class SecurityValidator:
    """Validator for security-related configuration settings."""

    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
        self.validation_results: List[ValidationResult] = []





    def _get_nested_value_safe(self, key: str, default: Any = None) -> Any:
        """Safely get a nested value from configuration."""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def _has_nested_key(self, key: str) -> bool:
        """Check if a nested key exists in configuration."""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False
        
        return True

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL has valid format."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
