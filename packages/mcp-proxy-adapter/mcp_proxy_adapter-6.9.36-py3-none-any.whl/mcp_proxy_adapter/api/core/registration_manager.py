"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Registration management utilities for MCP Proxy Adapter API.
"""

import os
import socket
import asyncio
from typing import Dict, Any, Optional

from mcp_proxy_adapter.core.logging import get_global_logger
from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient


class RegistrationManager:
    """Manager for proxy registration functionality using JsonRpcClient."""

    def __init__(self):
        """Initialize registration manager."""
        self.logger = get_global_logger()
        self.registered = False
        self.registration_task: Optional[asyncio.Task] = None
        self.server_name: Optional[str] = None
        self.server_url: Optional[str] = None
        self.proxy_url: Optional[str] = None
        self.capabilities: list = []
        self.metadata: Dict[str, Any] = {}

    async def register_with_proxy(self, config: Dict[str, Any]) -> bool:
        """Register this server with the proxy using JsonRpcClient."""
        try:
            proxy_config = config.get("proxy_registration", {})
            if not proxy_config.get("enabled", False):
                self.logger.info("Proxy registration disabled")
                return True

            proxy_url = proxy_config.get("proxy_url") or proxy_config.get("server_url")
            if not proxy_url:
                self.logger.warning("No proxy server URL configured")
                return False

            # Get server info
            server_config = config.get("server", {})
            host = server_config.get("host", "127.0.0.1")
            port = server_config.get("port", 8000)
            protocol = server_config.get("protocol", "http")

            # Use advertised host if available
            advertised_host = server_config.get("advertised_host") or host
            scheme = "https" if protocol in ("https", "mtls") else "http"
            advertised_url = f"{scheme}://{advertised_host}:{port}"

            # Get server name from config or generate default
            server_name = (
                proxy_config.get("server_id")
                or proxy_config.get("server_name")
                or f"mcp-adapter-{host}-{port}"
            )

            self.server_name = server_name
            self.server_url = advertised_url
            self.proxy_url = proxy_url

            # Get capabilities and metadata
            self.capabilities = proxy_config.get("capabilities", ["jsonrpc", "health"])
            self.metadata = {
                "uuid": config.get("uuid"),
                "protocol": protocol,
                "host": host,
                "port": port,
                **(proxy_config.get("metadata") or {}),
            }

            # Extract SSL certificates from proxy_registration config
            cert_file = None
            key_file = None
            ca_cert = None
            verify_ssl = True

            cert_config = proxy_config.get("certificate", {})
            ssl_config = proxy_config.get("ssl", {})

            if cert_config:
                cert_file = cert_config.get("cert_file")
                key_file = cert_config.get("key_file")

            if ssl_config:
                ca_cert = ssl_config.get("ca_cert")
                verify_mode = ssl_config.get("verify_mode", "CERT_REQUIRED")
                # If verify_mode is CERT_NONE, disable verification
                if verify_mode == "CERT_NONE":
                    verify_ssl = False
                elif ca_cert:
                    verify_ssl = ca_cert

            # Prepare client certificate tuple
            ssl_cert = None
            if cert_file and key_file:
                from pathlib import Path

                if Path(cert_file).exists() and Path(key_file).exists():
                    ssl_cert = (
                        str(Path(cert_file).absolute()),
                        str(Path(key_file).absolute()),
                    )

            # Use JsonRpcClient for registration (run in executor as it's synchronous)
            loop = asyncio.get_event_loop()
            client = JsonRpcClient(
                protocol="http", host="127.0.0.1", port=8080
            )  # Dummy, just for methods

            # Register synchronously in executor
            def _register():
                self.logger.info(
                    f"🔐 Registration SSL config: cert={ssl_cert is not None}, verify={verify_ssl}"
                )
                return client.register_with_proxy(
                    proxy_url=proxy_url,
                    server_name=server_name,
                    server_url=advertised_url,
                    capabilities=self.capabilities,
                    metadata=self.metadata,
                    cert=ssl_cert,
                    verify=verify_ssl,
                )

            try:
                result = await loop.run_in_executor(None, _register)
                self.logger.info(
                    f"✅ Successfully registered with proxy as {server_name} -> {advertised_url}"
                )
                self.registered = True
                return True
            except Exception as exc:
                self.logger.error(f"❌ Failed to register with proxy: {exc}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Registration error: {e}")
            return False

    async def start_heartbeat(self, config: Dict[str, Any]) -> None:
        """Start heartbeat task using JsonRpcClient."""
        if (
            not self.registered
            or not self.proxy_url
            or not self.server_name
            or not self.server_url
        ):
            return

        proxy_config = config.get("proxy_registration", {})
        heartbeat_config = proxy_config.get("heartbeat", {}) or {}
        heartbeat_interval = heartbeat_config.get(
            "interval", proxy_config.get("heartbeat_interval", 30)
        )

        self.logger.info(
            f"💓 Starting heartbeat task (interval: {heartbeat_interval}s)"
        )

        async def heartbeat_loop():
            # Extract SSL certificates from config
            proxy_config = config.get("proxy_registration", {})
            cert_file = None
            key_file = None
            ca_cert = None
            verify_ssl = True

            cert_config = proxy_config.get("certificate", {})
            ssl_config = proxy_config.get("ssl", {})

            if cert_config:
                cert_file = cert_config.get("cert_file")
                key_file = cert_config.get("key_file")

            if ssl_config:
                ca_cert = ssl_config.get("ca_cert")
                verify_mode = ssl_config.get("verify_mode", "CERT_REQUIRED")
                if verify_mode == "CERT_NONE":
                    verify_ssl = False
                elif ca_cert:
                    verify_ssl = ca_cert

            ssl_cert = None
            if cert_file and key_file:
                from pathlib import Path

                if Path(cert_file).exists() and Path(key_file).exists():
                    ssl_cert = (
                        str(Path(cert_file).absolute()),
                        str(Path(key_file).absolute()),
                    )

            loop = asyncio.get_event_loop()
            client = JsonRpcClient(
                protocol="http", host="127.0.0.1", port=8080
            )  # Dummy, just for methods

            def _heartbeat():
                return client.heartbeat_to_proxy(
                    proxy_url=self.proxy_url,
                    server_name=self.server_name,
                    server_url=self.server_url,
                    capabilities=self.capabilities,
                    metadata=self.metadata,
                    cert=ssl_cert,
                    verify=verify_ssl,
                )

            while True:
                try:
                    await asyncio.sleep(max(2, heartbeat_interval))
                    await loop.run_in_executor(None, _heartbeat)
                    self.logger.debug("💓 Heartbeat sent successfully")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {e}")

        self.registration_task = asyncio.create_task(heartbeat_loop())

    async def stop(self) -> None:
        """Stop registration manager and unregister from proxy."""
        # Cancel heartbeat task
        if self.registration_task:
            self.registration_task.cancel()
            try:
                await self.registration_task
            except asyncio.CancelledError:
                pass

        # Unregister from proxy if registered
        if self.registered and self.proxy_url and self.server_name:
            try:
                # Extract SSL certificates from config (use same logic as register)
                # Note: config needs to be passed to stop() method or stored in instance
                # For now, we'll try to use defaults or skip SSL if not available
                ssl_cert = None
                verify_ssl = True

                loop = asyncio.get_event_loop()
                client = JsonRpcClient(
                    protocol="http", host="127.0.0.1", port=8080
                )  # Dummy, just for methods

                def _unregister():
                    return client.unregister_from_proxy(
                        proxy_url=self.proxy_url,
                        server_name=self.server_name,
                        cert=ssl_cert,
                        verify=verify_ssl,
                    )

                await loop.run_in_executor(None, _unregister)
                self.logger.info(f"🛑 Unregistered from proxy: {self.server_name}")
            except Exception as e:
                self.logger.error(f"Error unregistering from proxy: {e}")

        self.registered = False
