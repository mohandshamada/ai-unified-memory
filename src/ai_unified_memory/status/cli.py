"""TTY dashboard for agent status."""

from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .checks import run_all_checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Status - Check all your agents")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Watch mode (refresh every 5 seconds)",
    )

    args = parser.parse_args()

    if args.json:
        results = run_all_checks()
        output = [
            {
                "name": r.name,
                "status": r.status,
                "message": r.message,
                "details": r.details,
            }
            for r in results
        ]
        print(json.dumps(output, indent=2))
        return 0

    console = Console()

    if args.watch:
        import time
        try:
            while True:
                console.clear()
                render_dashboard(console)
                time.sleep(5)
        except KeyboardInterrupt:
            return 0
    else:
        render_dashboard(console)

    return 0


def render_dashboard(console: Console) -> None:
    """Render the status dashboard."""
    results = run_all_checks()

    # Header
    ok_count = sum(1 for r in results if r.status == "ok")
    warning_count = sum(1 for r in results if r.status == "warning")
    error_count = sum(1 for r in results if r.status == "error")

    header_text = Text()
    header_text.append("Agent Status Dashboard", style="bold cyan")
    header_text.append(f"  |  ", style="dim")
    header_text.append(f"✅ {ok_count}  ", style="green")
    if warning_count:
        header_text.append(f"⚠️ {warning_count}  ", style="yellow")
    if error_count:
        header_text.append(f"❌ {error_count}  ", style="red")

    console.print(Panel(header_text, border_style="cyan"))
    console.print()

    # Status table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Agent", style="cyan", width=20)
    table.add_column("Status", width=10)
    table.add_column("Message", style="white")

    for result in results:
        status_emoji = {
            "ok": "✅",
            "warning": "⚠️",
            "error": "❌",
        }.get(result.status, "❓")

        status_color = {
            "ok": "green",
            "warning": "yellow",
            "error": "red",
        }.get(result.status, "white")

        table.add_row(
            result.name,
            f"[{status_color}]{status_emoji} {result.status.upper()}[/{status_color}]",
            result.message,
        )

    console.print(table)
    console.print()

    # Details panels
    for result in results:
        if result.details:
            details_text = "\n".join(
                f"[dim]{k}:[/dim] {v}" for k, v in result.details.items()
            )
            border = {
                "ok": "green",
                "warning": "yellow",
                "error": "red",
            }.get(result.status, "white")
            console.print(Panel(details_text, title=result.name, border_style=border))

    if all(r.status == "ok" for r in results):
        console.print()
        console.print("[green bold]All systems operational.[/green bold]")
    elif any(r.status == "error" for r in results):
        console.print()
        console.print("[red bold]Some systems need attention.[/red bold]")
