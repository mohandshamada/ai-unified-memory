"""CLI entry point for AI Unified Memory."""

from __future__ import annotations

import sys

import typer

from .server import run_sse, run_stdio

app = typer.Typer(help="AI Unified Memory - MCP server for shared agent memory")


@app.command()
def stdio() -> None:
    """Run the MCP server over stdio (for MCP clients)."""
    run_stdio()


@app.command()
def sse(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8080, help="Port to bind to"),
) -> None:
    """Run the MCP server over SSE (for HTTP clients)."""
    run_sse(host=host, port=port)


@app.command()
def info() -> None:
    """Show server info."""
    from .store import DEFAULT_MEMORY_PATH

    typer.echo(f"AI Unified Memory v0.1.0")
    typer.echo(f"Memory path: {DEFAULT_MEMORY_PATH}")
    typer.echo(f"Use 'aimemory stdio' to start the MCP server.")


@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without doing it"),
) -> None:
    """Sync agent-native paths with canonical store."""
    from .sync import ensure_symlinks

    results = ensure_symlinks(dry_run=dry_run)
    if dry_run:
        typer.echo("DRY RUN: No changes made.")

    if results["created_symlinks"]:
        typer.echo("Created symlinks:")
        for link in results["created_symlinks"]:
            typer.echo(f"  - {link}")
    else:
        typer.echo("All symlinks are already in place.")


@app.command()
def drift_check() -> None:
    """Check for drift between agent paths and store."""
    from .sync import check_drift

    results = check_drift()
    if not results:
        typer.echo("✅ No drift detected.")
    else:
        typer.echo("❌ Drift detected in the following files:")
        for drift in results:
            typer.echo(f"  - {drift.description}")
            typer.echo(f"    Agent path: {drift.agent_path}")


@app.command()
def repair() -> None:
    """Repair drift by merging or overwriting."""
    from .sync import repair_drift

    results = repair_drift()
    if results["drift_repaired"] > 0:
        typer.echo(f"Successfully repaired {results['drift_repaired']} files.")
    else:
        typer.echo("No drift to repair.")


def main() -> None:
    # Default to stdio if no command provided (for MCP compatibility)
    if len(sys.argv) == 1:
        run_stdio()
    else:
        app()
