"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

CLI command: config validate (Simple configuration validation)
"""

from __future__ import annotations

import sys
from argparse import Namespace

from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.core.config.simple_config_validator import SimpleConfigValidator


def config_validate_command(args: Namespace) -> int:
    cfg = SimpleConfig(args.file)
    try:
        model = cfg.load()
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return 1

    validator = SimpleConfigValidator()
    errors = validator.validate(model)
    if errors:
        print("❌ Validation failed:")
        for err in errors:
            print(f"   - {err.message}")
        return 1

    print("✅ Validation OK")
    return 0


