"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Simple synchronous JSON-RPC client for MCP alternatives Adapter.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class JsonRpcClient:
    """Simple synchronous JSON-RPC client."""

    def __init__(
        self,
        protocol: str = "http",
        host: str = "127.0.0.1",
        port: int = 8080,
        token_header: Optional[str] = None,
        token: Optional[str] = None,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        ca: Optional[str] = None,
    ):
        """
        Initialize JSON-RPC client.

        Args:
            protocol: Protocol (http or https)
            host: Server host
            port: Server port
            token_header: Token header name (e.g., "X-API-Key")
            token: Token value
            cert: Client certificate file path
            key: Client key file path
            ca: CA certificate file path
        """
        scheme = "https" if protocol == "https" else "http"
        self.base_url = f"{scheme}://{host}:{port}"

        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        if token_header and token:
            self.headers[token_header] = token

        self.verify = True
        self.cert: Optional[tuple[str, str] | None] = None

        if protocol == "https":
            if cert and key:
                self.cert = (str(Path(cert)), str(Path(key)))
            if ca:
                self.verify = str(Path(ca))
            else:
                self.verify = False  # Allow self-signed for examples

        self.timeout = 30

    def health(self) -> Dict[str, Any]:
        """Get server health status."""
        r = requests.get(
            f"{self.base_url}/health",
            headers=self.headers,
            timeout=self.timeout,
            verify=self.verify,
            cert=self.cert,
        )
        r.raise_for_status()
        return r.json()

    def jsonrpc_call(
        self, method: str, params: Dict[str, Any], req_id: int = 1
    ) -> Dict[str, Any]:
        """
        Make JSON-RPC call.

        Args:
            method: Method name
            params: Method parameters
            req_id: Request ID

        Returns:
            JSON-RPC response
        """
        payload: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": req_id,
        }
        r = requests.post(
            f"{self.base_url}/api/jsonrpc",
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
            verify=self.verify,
            cert=self.cert,
        )
        r.raise_for_status()
        return r.json()

    def _extract_result(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract result from JSON-RPC response, raising on error."""
        if "error" in response:
            error = response["error"]
            raise RuntimeError(
                f"JSON-RPC error: {error.get('message', 'Unknown error')} (code: {error.get('code', -1)})"
            )
        return response.get("result", {})

    # Built-in commands

    def echo(
        self, message: str = "Hello, World!", timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute echo command.

        Args:
            message: Message to echo
            timestamp: Optional timestamp

        Returns:
            Echo command result
        """
        params = {"message": message}
        if timestamp:
            params["timestamp"] = timestamp
        response = self.jsonrpc_call("echo", params)
        return self._extract_result(response)

    def help(self, command_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get help information.

        Args:
            command_name: Optional command name to get help for

        Returns:
            Help information
        """
        params = {}
        if command_name:
            params["command"] = command_name
        response = self.jsonrpc_call("help", params)
        return self._extract_result(response)

    def get_config(self) -> Dict[str, Any]:
        """
        Get server configuration.

        Returns:
            Server configuration
        """
        response = self.jsonrpc_call("config", {})
        return self._extract_result(response)

    def long_task(self, seconds: int) -> Dict[str, Any]:
        """
        Start a long-running task.

        Args:
            seconds: Task duration in seconds

        Returns:
            Task result with job_id
        """
        response = self.jsonrpc_call("long_task", {"seconds": seconds})
        return self._extract_result(response)

    def job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status information
        """
        response = self.jsonrpc_call("job_status", {"job_id": job_id})
        return self._extract_result(response)

    # Queue management commands

    def queue_health(self) -> Dict[str, Any]:
        """
        Get queue manager health status.

        Returns:
            Queue health information
        """
        response = self.jsonrpc_call("queue_health", {})
        return self._extract_result(response)

    def queue_add_job(
        self,
        job_type: str,
        job_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add a job to the queue.

        Args:
            job_type: Type of job (data_processing, file_operation, api_call, custom, long_running, batch_processing, file_download)
            job_id: Unique job identifier
            params: Job-specific parameters

        Returns:
            Job addition result
        """
        response = self.jsonrpc_call(
            "queue_add_job",
            {
                "job_type": job_type,
                "job_id": job_id,
                "params": params,
            },
        )
        return self._extract_result(response)

    def queue_start_job(self, job_id: str) -> Dict[str, Any]:
        """
        Start a job in the queue.

        Args:
            job_id: Job identifier

        Returns:
            Job start result
        """
        response = self.jsonrpc_call("queue_start_job", {"job_id": job_id})
        return self._extract_result(response)

    def queue_stop_job(self, job_id: str) -> Dict[str, Any]:
        """
        Stop a running job.

        Args:
            job_id: Job identifier

        Returns:
            Job stop result
        """
        response = self.jsonrpc_call("queue_stop_job", {"job_id": job_id})
        return self._extract_result(response)

    def queue_delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Delete a job from the queue.

        Args:
            job_id: Job identifier

        Returns:
            Job deletion result
        """
        response = self.jsonrpc_call("queue_delete_job", {"job_id": job_id})
        return self._extract_result(response)

    def queue_get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a specific job.

        Args:
            job_id: Job identifier

        Returns:
            Job status information
        """
        response = self.jsonrpc_call("queue_get_job_status", {"job_id": job_id})
        return self._extract_result(response)

    def queue_list_jobs(
        self, status: Optional[str] = None, job_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all jobs in the queue.

        Args:
            status: Optional filter by status (pending, running, completed, failed, stopped)
            job_type: Optional filter by job type

        Returns:
            List of jobs
        """
        params = {}
        if status:
            params["status"] = status
        if job_type:
            params["job_type"] = job_type
        response = self.jsonrpc_call("queue_list_jobs", params)
        return self._extract_result(response)

    # Proxy registration methods

    def register_with_proxy(
        self,
        proxy_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cert: Optional[tuple[str, str]] = None,
        verify: Optional[bool | str] = None,
    ) -> Dict[str, Any]:
        """
        Register this server with a proxy server.

        Args:
            proxy_url: URL of the proxy server (e.g., "http://localhost:3005")
            server_name: Name/ID of this server
            server_url: URL where this server is accessible
            capabilities: Optional list of server capabilities
            metadata: Optional metadata dictionary
            cert: Optional tuple of (cert_file, key_file) for client certificates
            verify: Optional SSL verification (True, False, or path to CA cert)

        Returns:
            Registration result
        """
        payload = {
            "server_id": server_name,
            "server_url": server_url,
        }

        # Use provided SSL settings or fall back to instance settings
        ssl_verify = verify if verify is not None else self.verify
        ssl_cert = cert if cert is not None else self.cert

        proxy_base = proxy_url.rstrip("/")
        r = requests.post(
            f"{proxy_base}/register",
            json=payload,
            timeout=10,
            verify=ssl_verify,
            cert=ssl_cert,
        )

        # Check if server is already registered (400 with "already registered" message)
        if r.status_code == 400:
            error_data = r.json()
            error_msg = error_data.get("error", "").lower()
            if "already registered" in error_msg:
                # Server is already registered - extract server_key from error and unregister
                import re

                # Extract server_key from error message: "already registered as <server_key>"
                match = re.search(
                    r"already registered as ([^\s,]+)",
                    error_data.get("error", ""),
                    re.IGNORECASE,
                )
                if match:
                    registered_server_key = match.group(1)
                    try:
                        # Extract original server_id by removing suffix (e.g., "_1", "_2")
                        # If server_key is "test-inspect-2_1", original server_id is "test-inspect-2"
                        original_server_id = registered_server_key
                        if "_" in registered_server_key:
                            # Remove suffix like "_1", "_2", etc.
                            original_server_id = re.sub(
                                r"_\d+$", "", registered_server_key
                            )

                        # Unregister using the original server_id (without suffix)
                        unregister_payload = {
                            "server_id": original_server_id,
                            "server_url": "",
                        }
                        unregister_response = requests.post(
                            f"{proxy_base}/unregister",
                            json=unregister_payload,
                            timeout=10,
                            verify=ssl_verify,
                            cert=ssl_cert,
                        )
                        # Only retry if unregister was successful
                        if unregister_response.status_code == 200:
                            # Retry registration after successful unregistering
                            r = requests.post(
                                f"{proxy_base}/register",
                                json=payload,
                                timeout=10,
                                verify=ssl_verify,
                                cert=ssl_cert,
                            )
                    except Exception:
                        # If unregister/register fails, ignore and continue with original response
                        pass

        r.raise_for_status()
        return r.json()

    def unregister_from_proxy(
        self,
        proxy_url: str,
        server_name: str,
        cert: Optional[tuple[str, str]] = None,
        verify: Optional[bool | str] = None,
    ) -> Dict[str, Any]:
        """
        Unregister this server from a proxy server.

        Args:
            proxy_url: URL of the proxy server (e.g., "http://localhost:3005")
            server_name: Name/ID of this server
            cert: Optional tuple of (cert_file, key_file) for client certificates
            verify: Optional SSL verification (True, False, or path to CA cert)

        Returns:
            Unregistration result
        """
        payload = {
            "server_id": server_name,
            "server_url": "",
        }

        # Use provided SSL settings or fall back to instance settings
        ssl_verify = verify if verify is not None else self.verify
        ssl_cert = cert if cert is not None else self.cert

        proxy_base = proxy_url.rstrip("/")
        r = requests.post(
            f"{proxy_base}/unregister",
            json=payload,
            timeout=10,
            verify=ssl_verify,
            cert=ssl_cert,
        )
        r.raise_for_status()
        return r.json()

    def heartbeat_to_proxy(
        self,
        proxy_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cert: Optional[tuple[str, str]] = None,
        verify: Optional[bool | str] = None,
    ) -> Dict[str, Any]:
        """
        Send heartbeat to proxy server.

        Args:
            proxy_url: URL of the proxy server (e.g., "http://localhost:3005")
            server_name: Name/ID of this server
            server_url: URL where this server is accessible
            capabilities: Optional list of server capabilities
            metadata: Optional metadata dictionary
            cert: Optional tuple of (cert_file, key_file) for client certificates
            verify: Optional SSL verification (True, False, or path to CA cert)

        Returns:
            Heartbeat result
        """
        payload = {
            "server_id": server_name,
            "server_url": server_url,
        }

        # Use provided SSL settings or fall back to instance settings
        ssl_verify = verify if verify is not None else self.verify
        ssl_cert = cert if cert is not None else self.cert

        proxy_base = proxy_url.rstrip("/")
        r = requests.post(
            f"{proxy_base}/proxy/heartbeat",
            json=payload,
            timeout=10,
            verify=ssl_verify,
            cert=ssl_cert,
        )
        r.raise_for_status()
        return r.json()

    def list_proxy_servers(self, proxy_url: str) -> Dict[str, Any]:
        """
        List all servers registered on a proxy server.

        Args:
            proxy_url: URL of the proxy server (e.g., "http://localhost:3005")

        Returns:
            List of registered servers
        """
        proxy_base = proxy_url.rstrip("/")
        r = requests.get(f"{proxy_base}/proxy/list", timeout=10)
        r.raise_for_status()
        return r.json()

    def get_proxy_health(self, proxy_url: str) -> Dict[str, Any]:
        """
        Get proxy server health status.

        Args:
            proxy_url: URL of the proxy server (e.g., "http://localhost:3005")

        Returns:
            Proxy health status
        """
        proxy_base = proxy_url.rstrip("/")
        r = requests.get(f"{proxy_base}/proxy/health", timeout=10)
        r.raise_for_status()
        return r.json()
