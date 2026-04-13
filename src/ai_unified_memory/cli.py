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


def main() -> None:
    # Default to stdio if no command provided (for MCP compatibility)
    if len(sys.argv) == 1:
        run_stdio()
    else:
        app()
