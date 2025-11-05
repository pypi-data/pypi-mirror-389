"""
Server Engine Abstraction

This module provides an abstraction layer for the hypercorn ASGI server engine,
providing full mTLS support and SSL capabilities.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict

from .logging import get_global_logger

logger = logging.getLogger(__name__)


class ServerEngine(ABC):
    """
    Abstract base class for server engines.

    This class defines the interface that all server engines must implement,
    allowing the framework to work with different ASGI servers transparently.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the server engine."""
        pass

    @abstractmethod
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get supported features of this server engine.

        Returns:
            Dictionary mapping feature names to boolean support status
        """
        pass


class HypercornEngine(ServerEngine):
    """
    Hypercorn server engine implementation.

    Provides full mTLS support and better SSL capabilities.
    """

    def get_name(self) -> str:
        return "hypercorn"

    def get_supported_features(self) -> Dict[str, bool]:
        return {
            "ssl_tls": True,
            "mtls_client_certs": True,  # Full support
            "ssl_scope_info": True,  # SSL info in request scope
            "client_cert_verification": True,
            "websockets": True,
            "http2": True,
            "reload": True,
        }


class ServerEngineFactory:
    """
    Factory for creating server engines.

    This class manages the creation and configuration of different server engines.
    """

    _engines: Dict[str, ServerEngine] = {}

    @classmethod
    def register_engine(cls, engine: ServerEngine) -> None:
        """
        Register a server engine.

        Args:
            engine: Server engine instance to register
        """
        cls._engines[engine.get_name()] = engine
        get_global_logger().info(f"Registered server engine: {engine.get_name()}")

    @classmethod
    def initialize_default_engines(cls) -> None:
        """Initialize default server engines."""
        # Register hypercorn engine (only supported engine)
        try:
            import hypercorn  # noqa: F401

            cls.register_engine(HypercornEngine())
            get_global_logger().info(
                "Hypercorn engine registered (full mTLS support available)"
            )
        except ImportError:
            get_global_logger().error(
                "Hypercorn not available - this is required for the framework"
            )
            raise


# Initialize default engines
ServerEngineFactory.initialize_default_engines()
