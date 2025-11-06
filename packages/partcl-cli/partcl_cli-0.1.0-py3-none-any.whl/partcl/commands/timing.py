"""
Timing analysis command for the Partcl CLI.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from tabulate import tabulate

from partcl.client.api import APIClient
from partcl.utils.validation import validate_file


@click.command()
@click.option(
    "--verilog-file",
    "-v",
    required=True,
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to Verilog design file (.v)",
)
@click.option(
    "--lib-file",
    "-l",
    required=True,
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to Liberty timing library (.lib)",
)
@click.option(
    "--sdc-file",
    "-s",
    required=True,
    type=click.Path(exists=True, readable=True, path_type=Path),
    help="Path to Synopsys Design Constraints file (.sdc)",
)
@click.option(
    "--local",
    is_flag=True,
    default=False,
    envvar="PARTCL_LOCAL",
    help="Use local server instead of cloud",
)
@click.option(
    "--token",
    envvar="PARTCL_TOKEN",
    help="JWT authentication token for cloud service",
)
@click.option(
    "--url",
    envvar="PARTCL_API_URL",
    help="Override API base URL",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table"], case_sensitive=False),
    default="table",
    envvar="PARTCL_OUTPUT_FORMAT",
    help="Output format",
)
@click.option(
    "--timeout",
    type=int,
    default=300,
    help="Request timeout in seconds",
)
@click.pass_context
def timing(
    ctx: click.Context,
    verilog_file: Path,
    lib_file: Path,
    sdc_file: Path,
    local: bool,
    token: Optional[str],
    url: Optional[str],
    output: str,
    timeout: int,
) -> None:
    """
    Run timing analysis on a digital design.

    Analyzes timing using a Verilog netlist, Liberty library, and SDC constraints.
    Can run against either the cloud service (default) or a local Docker container.

    Examples:

        # Cloud mode (default)
        partcl timing -v design.v -l library.lib -s constraints.sdc

        # Local mode (Docker)
        partcl timing -v design.v -l library.lib -s constraints.sdc --local

        # Custom server
        partcl timing -v design.v -l library.lib -s constraints.sdc --url http://myserver:8000

        # JSON output
        partcl timing -v design.v -l library.lib -s constraints.sdc --output json
    """
    console: Console = ctx.obj["console"]

    # Validate input files
    try:
        if output.lower() != "json":
            console.print("[cyan]Validating input files...[/cyan]")
        validate_file(verilog_file, ".v")
        validate_file(lib_file, ".lib")
        validate_file(sdc_file, ".sdc")
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        sys.exit(1)

    # Determine API URL
    if url:
        api_url = url
    elif local:
        api_url = "http://localhost:8000"
    else:
        # Default Modal URL
        api_url = "https://partcl--boson-eda-processor-web.modal.run"

    # Check authentication for cloud mode
    if not local and not token:
        console.print(
            "[yellow]Warning: No authentication token provided for cloud service.[/yellow]"
        )
        console.print("Set PARTCL_TOKEN environment variable or use --token flag.")
        if not click.confirm("Continue without authentication?"):
            sys.exit(1)

    # Create API client
    client = APIClient(base_url=api_url, token=token, timeout=timeout)

    # Check if server supports local mode
    use_local_mode = False
    if local or url:
        try:
            use_local_mode = client.check_local_mode()
            if use_local_mode and output.lower() != "json":
                console.print("[cyan]Server supports local mode (zero-copy file access)[/cyan]")
        except Exception:
            if output.lower() != "json":
                console.print("[yellow]Could not detect server mode, using upload mode[/yellow]")

    # Display connection info
    if output.lower() != "json":
        console.print(f"\n[cyan]Connecting to:[/cyan] {api_url}")
        console.print(f"[cyan]Mode:[/cyan] {'Local' if local else 'Cloud'}")
        console.print(f"[cyan]File Transfer:[/cyan] {'Path-based (zero-copy)' if use_local_mode else 'Upload'}")
        console.print(f"[cyan]Authentication:[/cyan] {'Enabled' if token else 'Disabled'}")
        console.print()

    # Prepare file paths or contents based on mode
    if use_local_mode:
        # Local mode: send absolute paths
        if output.lower() != "json":
            console.print("[cyan]Preparing file paths for local mode...[/cyan]")
        try:
            verilog_path = str(verilog_file.resolve())
            lib_path = str(lib_file.resolve())
            sdc_path = str(sdc_file.resolve())

            # Display paths
            if output.lower() != "json":
                console.print(f"  Verilog: {verilog_path}")
                console.print(f"  Liberty: {lib_path}")
                console.print(f"  SDC: {sdc_path}")
                console.print()
        except Exception as e:
            console.print(f"[red]Error resolving paths: {e}[/red]")
            sys.exit(1)
    else:
        # Upload mode: read file contents
        if output.lower() != "json":
            console.print("[cyan]Reading input files...[/cyan]")
        try:
            verilog_content = verilog_file.read_bytes()
            lib_content = lib_file.read_bytes()
            sdc_content = sdc_file.read_bytes()

            # Display file sizes
            if output.lower() != "json":
                console.print(f"  Verilog: {verilog_file.name} ({len(verilog_content):,} bytes)")
                console.print(f"  Liberty: {lib_file.name} ({len(lib_content):,} bytes)")
                console.print(f"  SDC: {sdc_file.name} ({len(sdc_content):,} bytes)")
                console.print()
        except IOError as e:
            console.print(f"[red]Error reading files: {e}[/red]")
            sys.exit(1)

    # Run timing analysis with progress indicator
    if output.lower() != "json":
        console.print("[cyan]Running timing analysis...[/cyan]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing design...", total=None)

            # Call appropriate API method based on mode
            if use_local_mode:
                result = client.analyze_timing_local(
                    verilog_path=verilog_path,
                    lib_path=lib_path,
                    sdc_path=sdc_path,
                )
            else:
                result = client.analyze_timing(
                    verilog_content=verilog_content,
                    lib_content=lib_content,
                    sdc_content=sdc_content,
                    verilog_filename=verilog_file.name,
                    lib_filename=lib_file.name,
                    sdc_filename=sdc_file.name,
                )

            progress.update(task, completed=100)
    except Exception as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        sys.exit(1)

    # Check if analysis was successful
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        console.print(f"[red]Analysis failed: {error_msg}[/red]")
        sys.exit(1)

    # Get violations count for exit code
    violations = result.get("num_violations", 0)

    # Display results
    if output.lower() != "json":
        console.print()
    if output.lower() == "json":
        # JSON output
        console.print(json.dumps(result, indent=2))
    else:
        # Table output
        console.print("[green]Timing Analysis Results[/green]")
        console.print("=" * 40)

        # Create results table
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        # Add timing metrics
        wns = result.get("wns", 0)
        tns = result.get("tns", 0)
        endpoints = result.get("total_endpoints", 0)

        table.add_row("Worst Negative Slack", f"{wns:.2f} ps")
        table.add_row("Total Negative Slack", f"{tns:.2f} ps")
        table.add_row("Timing Violations", str(violations))
        table.add_row("Total Endpoints", str(endpoints))

        # Add deployment info if available
        if "deployment" in result:
            table.add_row("Deployment", result["deployment"])
        if "gpu_available" in result:
            table.add_row("GPU Available", str(result["gpu_available"]))

        console.print(table)

        # Add summary
        console.print()
        if violations == 0:
            console.print("[green]✓ Design meets timing requirements[/green]")
        else:
            console.print(f"[yellow]⚠ Design has {violations} timing violation(s)[/yellow]")

    # Exit with appropriate code
    sys.exit(0 if violations == 0 else 1)