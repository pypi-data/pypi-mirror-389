"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Simple configuration generator for MCP Proxy Adapter.
"""

from __future__ import annotations

from typing import Optional

from .simple_config import (
    SimpleConfig,
    SimpleConfigModel,
    ServerConfig,
    ProxyClientConfig,
    AuthConfig,
)


class SimpleConfigGenerator:
    """Generate minimal configuration according to the plan."""

    def generate(self, protocol: str, with_proxy: bool = False, out_path: str = "config.json") -> str:
        server = ServerConfig(host="0.0.0.0", port=8080, protocol=protocol)
        if protocol in ("https", "mtls"):
            server.cert_file = "./certs/server.crt"
            server.key_file = "./certs/server.key"
        if protocol == "mtls":
            server.ca_cert_file = "./certs/ca.crt"

        proxy = ProxyClientConfig(enabled=with_proxy)
        if with_proxy:
            proxy.protocol = protocol
            proxy.host = "localhost"
            proxy.port = 3005
            if protocol in ("https", "mtls"):
                proxy.cert_file = "./certs/client.crt"
                proxy.key_file = "./certs/client.key"
            if protocol == "mtls":
                proxy.ca_cert_file = "./certs/ca.crt"

        auth = AuthConfig(use_token=False, use_roles=False, tokens={}, roles={})

        cfg = SimpleConfig()
        cfg.model = SimpleConfigModel(server=server, proxy_client=proxy, auth=auth)
        cfg.save(out_path)
        return out_path


