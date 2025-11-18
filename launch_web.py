#!/usr/bin/env python3
"""
Launch script for Meton Web UI.

Usage:
    python launch_web.py
    python launch_web.py --share
    python launch_web.py --auth username:password
    python launch_web.py --port 8080
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from web.app import MetonWebUI


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Launch Meton Web UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_web.py                    # Launch locally
  python launch_web.py --share            # Enable public sharing
  python launch_web.py --port 8080        # Custom port
  python launch_web.py --auth user:pass   # With authentication
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )

    parser.add_argument(
        "--share",
        action="store_true",
        help="Enable Gradio public sharing (creates public URL)"
    )

    parser.add_argument(
        "--auth",
        type=str,
        help="Authentication in format 'username:password'"
    )

    parser.add_argument(
        "--host",
        type=str,
        help="Host address (overrides config)"
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Port number (overrides config)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    print("🚀 Starting Meton Web UI...")
    print(f"   Config: {args.config}")

    # Create UI instance
    ui = MetonWebUI(config_path=args.config)

    # Parse authentication
    auth = None
    if args.auth:
        if ':' in args.auth:
            username, password = args.auth.split(':', 1)
            auth = (username, password)
            print(f"   Authentication: Enabled (user: {username})")
        else:
            print("❌ Error: Authentication must be in format 'username:password'")
            sys.exit(1)
    elif ui.config.config.web_ui.auth:
        # Use auth from config if available
        if ':' in ui.config.config.web_ui.auth:
            username, password = ui.config.config.web_ui.auth.split(':', 1)
            auth = (username, password)
            print(f"   Authentication: Enabled from config (user: {username})")

    # Prepare launch kwargs
    launch_kwargs = {}

    if args.host:
        launch_kwargs['server_name'] = args.host
        print(f"   Host: {args.host}")
    else:
        host = ui.config.config.web_ui.host
        launch_kwargs['server_name'] = host
        print(f"   Host: {host}")

    if args.port:
        launch_kwargs['server_port'] = args.port
        print(f"   Port: {args.port}")
    else:
        port = ui.config.config.web_ui.port
        launch_kwargs['server_port'] = port
        print(f"   Port: {port}")

    # Determine if sharing should be enabled
    share = args.share or ui.config.config.web_ui.share
    if share:
        print("   Sharing: Enabled (public URL will be generated)")

    if args.debug:
        launch_kwargs['debug'] = True
        print("   Debug: Enabled")

    print("\n✨ Launching interface...")
    print("   Press Ctrl+C to stop\n")

    try:
        ui.launch(share=share, auth=auth, **launch_kwargs)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Meton Web UI...")
        ui.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error launching Web UI: {e}")
        ui.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
