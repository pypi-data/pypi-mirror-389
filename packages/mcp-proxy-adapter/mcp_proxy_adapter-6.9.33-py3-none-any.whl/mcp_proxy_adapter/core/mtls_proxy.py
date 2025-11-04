"""
mTLS Proxy for MCP Proxy Adapter

This module provides mTLS proxy functionality that accepts mTLS connections
and proxies them to the internal hypercorn server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import ssl
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MTLSProxy:
    """
    mTLS Proxy that accepts mTLS connections and proxies them to internal server.
    """
    
    def __init__(self, 
                 external_host: str,
                 external_port: int,
                 internal_host: str = "127.0.0.1",
                 internal_port: int = 9000,
                 cert_file: Optional[str] = None,
                 key_file: Optional[str] = None,
                 ca_cert: Optional[str] = None):
        """
        Initialize mTLS Proxy.
        
        Args:
            external_host: External host to bind to
            external_port: External port to bind to
            internal_host: Internal server host
            internal_port: Internal server port
            cert_file: Server certificate file
            key_file: Server private key file
            ca_cert: CA certificate file for client verification
        """
        self.external_host = external_host
        self.external_port = external_port
        self.internal_host = internal_host
        self.internal_port = internal_port
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_cert = ca_cert
        self.server = None
        
    async def start(self):
        """Start the mTLS proxy server."""
        try:
            # Create SSL context
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.cert_file, self.key_file)
            
            if self.ca_cert:
                ssl_context.load_verify_locations(self.ca_cert)
                ssl_context.verify_mode = ssl.CERT_REQUIRED
            else:
                ssl_context.verify_mode = ssl.CERT_NONE
                
            # Start server
            self.server = await asyncio.start_server(
                self._handle_client,
                self.external_host,
                self.external_port,
                ssl=ssl_context
            )
            
            get_global_logger().info(f"🔐 mTLS Proxy started on {self.external_host}:{self.external_port}")
            get_global_logger().info(f"🌐 Proxying to {self.internal_host}:{self.internal_port}")
            
        except Exception as e:
            get_global_logger().error(f"❌ Failed to start mTLS proxy: {e}")
            raise
            
            
                
    async def _proxy_data(self, reader, writer, direction):
        """Proxy data between reader and writer."""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception as e:
            get_global_logger().debug(f"Proxy connection closed ({direction}): {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass


