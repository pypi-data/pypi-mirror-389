"""
Main entry point for the Partcl CLI.
"""

import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console

from partcl import __version__
from partcl.commands import auth, timing

# Load environment variables
load_dotenv(".partcl.env")
load_dotenv(Path.home() / ".partcl.env")

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="partcl")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Partcl CLI - GPU-accelerated EDA tools.

    Run timing analysis and circuit optimization on your designs
    using either cloud (Modal) or local (Docker) backends.
    """
    # Store console in context for use by subcommands
    ctx.ensure_object(dict)
    ctx.obj["console"] = console


# Register commands
cli.add_command(auth.login)
cli.add_command(timing.timing)


def main() -> int:
    """Main entry point for the CLI."""
    try:
        cli()
        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())