"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Simple configuration validator ensuring required fields and files exist.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from .simple_config import SimpleConfigModel


@dataclass
class ValidationError:
    message: str


class SimpleConfigValidator:
    """Validate SimpleConfigModel instances."""

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        errors: List[ValidationError] = []
        errors.extend(self._validate_server(model))
        errors.extend(self._validate_proxy_client(model))
        errors.extend(self._validate_auth(model))
        return errors

    def _validate_server(self, model: SimpleConfigModel) -> List[ValidationError]:
        e: List[ValidationError] = []
        s = model.server
        if not s.host:
            e.append(ValidationError("server.host is required"))
        if not isinstance(s.port, int):
            e.append(ValidationError("server.port must be integer"))
        if s.protocol not in ("http", "https", "mtls"):
            e.append(ValidationError("server.protocol must be one of: http, https, mtls"))
        if s.protocol in ("https", "mtls"):
            if not s.cert_file:
                e.append(ValidationError(f"server.cert_file is required for {s.protocol}"))
            if not s.key_file:
                e.append(ValidationError(f"server.key_file is required for {s.protocol}"))
        if s.protocol == "mtls" and not s.ca_cert_file:
            e.append(ValidationError("server.ca_cert_file is required for mtls"))
        # Files existence (if provided)
        for label, path in ("cert_file", s.cert_file), ("key_file", s.key_file), ("ca_cert_file", s.ca_cert_file), ("crl_file", s.crl_file):
            if path and not os.path.exists(path):
                e.append(ValidationError(f"server.{label} not found: {path}"))
        return e

    def _validate_proxy_client(self, model: SimpleConfigModel) -> List[ValidationError]:
        e: List[ValidationError] = []
        pc = model.proxy_client
        if pc.enabled:
            if not pc.host:
                e.append(ValidationError("proxy_client.host is required when enabled"))
            if not isinstance(pc.port, int):
                e.append(ValidationError("proxy_client.port must be integer"))
            if pc.protocol not in ("http", "https", "mtls"):
                e.append(ValidationError("proxy_client.protocol must be one of: http, https, mtls"))
            if pc.protocol in ("https", "mtls"):
                if not pc.cert_file:
                    e.append(ValidationError(f"proxy_client.cert_file is required for {pc.protocol}"))
                if not pc.key_file:
                    e.append(ValidationError(f"proxy_client.key_file is required for {pc.protocol}"))
            if pc.protocol == "mtls" and not pc.ca_cert_file:
                e.append(ValidationError("proxy_client.ca_cert_file is required for mtls"))
            # Files existence (if provided)
            for label, path in ("cert_file", pc.cert_file), ("key_file", pc.key_file), ("ca_cert_file", pc.ca_cert_file), ("crl_file", pc.crl_file):
                if path and not os.path.exists(path):
                    e.append(ValidationError(f"proxy_client.{label} not found: {path}"))
            # Heartbeat
            if not pc.heartbeat.endpoint:
                e.append(ValidationError("proxy_client.heartbeat.endpoint is required"))
            if not isinstance(pc.heartbeat.interval, int) or pc.heartbeat.interval <= 0:
                e.append(ValidationError("proxy_client.heartbeat.interval must be positive integer"))
            # Registration endpoints
            if not pc.registration.register_endpoint:
                e.append(ValidationError("proxy_client.registration.register_endpoint is required"))
            if not pc.registration.unregister_endpoint:
                e.append(ValidationError("proxy_client.registration.unregister_endpoint is required"))
        return e

    def _validate_auth(self, model: SimpleConfigModel) -> List[ValidationError]:
        e: List[ValidationError] = []
        a = model.auth
        if a.use_roles and not a.use_token:
            e.append(ValidationError("auth.use_roles requires auth.use_token to be true"))
        if a.use_token and not a.tokens:
            e.append(ValidationError("auth.tokens must be provided when auth.use_token is true"))
        return e


