"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

CLI command: config generate (Simple configuration generator)
"""

from __future__ import annotations

from argparse import Namespace

from mcp_proxy_adapter.core.config.simple_config_generator import SimpleConfigGenerator


def config_generate_command(args: Namespace) -> int:
    generator = SimpleConfigGenerator()
    out = generator.generate(protocol=args.protocol, with_proxy=args.with_proxy, out_path=args.out)
    print(f"✅ Configuration generated: {out}")
    return 0


