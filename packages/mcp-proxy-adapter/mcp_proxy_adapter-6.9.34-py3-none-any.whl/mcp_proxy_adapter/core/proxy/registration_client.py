"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Registration client for proxy registration.
"""

import time
import traceback

import aiohttp

from mcp_proxy_adapter.core.logging import get_global_logger
from .auth_manager import AuthManager
from .ssl_manager import SSLManager


class RegistrationClient:
    """Client for proxy registration operations."""

    def __init__(self, client_security, registration_config: Dict[str, Any], config: Dict[str, Any], proxy_url: str):
        """
        Initialize registration client.

        Args:
            client_security: Client security manager instance
            registration_config: Registration configuration
            config: Application configuration
            proxy_url: Proxy server URL
        """
        self.client_security = client_security
        self.registration_config = registration_config
        self.config = config
        self.proxy_url = proxy_url
        self.logger = get_global_logger()
        
        # Initialize managers
        self.auth_manager = AuthManager(client_security, registration_config)
        self.ssl_manager = SSLManager(client_security, registration_config, config, proxy_url)



    def _prepare_registration_data(self, server_url: str) -> Dict[str, Any]:
        """
        Prepare registration data.

        Args:
            server_url: Server URL to register

        Returns:
            Registration data dictionary
        """
        return {
            "server_id": self.registration_config.get("server_id"),
            "server_name": self.registration_config.get("server_name"),
            "server_url": server_url,
            "description": self.registration_config.get("description", ""),
            "version": self.registration_config.get("version", "1.0.0"),
            "capabilities": self.registration_config.get("capabilities", []),
        }
