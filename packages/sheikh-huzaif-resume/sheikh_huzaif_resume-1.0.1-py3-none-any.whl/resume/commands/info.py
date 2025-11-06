"""Info command implementation."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import questionary

console = Console()


def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed information"
    ),
):
    """
    Display information about the CLI tool.
    """

    table = Table(title="CLI Tool Information", border_style="cyan")
    
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    
    table.add_row("Name", "CLI Resume")
    table.add_row("Version", "1.0.0")
    table.add_row("Author", "Sheikh Huzaif")
    table.add_row("Language", "Python 🐍")
    
    if verbose:
        table.add_row("Framework", "Typer + Rich")
        table.add_row("License", "MIT")
    
    console.print(table)
    
    if not verbose:
        console.print("\n[dim]Tip: Use --verbose for more details[/dim]")