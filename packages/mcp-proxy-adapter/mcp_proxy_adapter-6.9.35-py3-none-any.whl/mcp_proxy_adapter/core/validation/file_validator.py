"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

File validation utilities for MCP Proxy Adapter configuration validation.
"""

import os
import ssl

from .validation_result import ValidationResult


class FileValidator:
    """Validator for file-related configuration settings."""

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

    def _is_file_required_for_enabled_features(self, file_key: str) -> bool:
        """Check if a file is required based on enabled features."""
        # SSL files are required if SSL is enabled
        if file_key.startswith("ssl.") or file_key.startswith("transport.ssl."):
            return self._get_nested_value_safe("ssl.enabled", False)
        
        # Proxy registration files are required if proxy registration is enabled
        if file_key.startswith("proxy_registration."):
            return self._get_nested_value_safe("proxy_registration.enabled", False)
        
        # Log directory is required if logging is enabled
        if file_key == "logging.log_dir":
            return self._get_nested_value_safe("logging.enabled", True)
        
        # Command directories are required if commands are enabled
        if file_key.startswith("commands."):
            return self._get_nested_value_safe("commands.enabled", True)
        
        # Security files are required if security is enabled
        if file_key.startswith("security."):
            return self._get_nested_value_safe("security.enabled", False)
        
        return False
