import argparse
import asyncio
import logging
import sys

from auth_proxy import version
from auth_proxy.auth_plugins import PLUGIN_REGISTRY
from auth_proxy.config import ProxyConfig
from auth_proxy.proxy import AuthProxy


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Modular Authenticating Reverse Proxy")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to config file"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="List available authentication plugins",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # List plugins if requested
    if args.list_plugins:
        print("Available authentication plugins:")
        for name in sorted(PLUGIN_REGISTRY.keys()):
            print(f"  - {name}")
        return

    try:
        # Load configuration
        config = ProxyConfig(args.config)

        # Create and start proxy
        proxy = AuthProxy(config.config)
        asyncio.run(proxy.start())
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
