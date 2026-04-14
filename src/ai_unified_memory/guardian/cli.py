"""CLI for Memory Guardian."""

from __future__ import annotations

import argparse
import sys

from .digest import format_digest, generate_digest
from .telegram import send_digest


def main() -> int:
    parser = argparse.ArgumentParser(description="Memory Guardian - Daily unified memory digest")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate digest but don't send to Telegram",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Send digest to Telegram",
    )

    args = parser.parse_args()

    # Generate digest
    digest = generate_digest()

    if args.format == "json":
        import json
        print(json.dumps(digest, indent=2))
        return 0

    # Format as text
    formatted = format_digest(digest)
    print(formatted)

    # Send to Telegram if requested
    if args.telegram and not args.dry_run:
        if send_digest(formatted):
            print("\n✅ Sent to Telegram")
        else:
            print("\n❌ Failed to send to Telegram")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
