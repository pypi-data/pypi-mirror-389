"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Lightweight client library for registry (proxy) server used in examples.
"""

from typing import Any, Dict, List, Optional

import requests


class ProxyClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/proxy/health", timeout=5)
        r.raise_for_status()
        return r.json()

    def register(self, name: str, url: str, capabilities: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"name": name, "url": url, "capabilities": capabilities or [], "metadata": metadata or {}}
        r = requests.post(f"{self.base_url}/register", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()

    def unregister(self, name: str) -> Dict[str, Any]:
        payload = {"name": name, "url": "", "capabilities": [], "metadata": {}}
        r = requests.post(f"{self.base_url}/unregister", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()

    def list_servers(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/proxy/list", timeout=5)
        r.raise_for_status()
        return r.json()

    def heartbeat(self, name: str, url: str) -> Dict[str, Any]:
        payload = {"name": name, "url": url, "capabilities": [], "metadata": {}}
        r = requests.post(f"{self.base_url}/proxy/heartbeat", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()


