"""Education command implementation."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import textwrap

from ..data import resume
console = Console()

def main(
        verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed information"
    ),
):
    """
    Education
    """
    education = resume.get("education")
    if not education:
        console.print("[bold red]No education records found.[/bold red]")
        return

    console.print("\n🎓 [bold underline bright_blue]Education[/bold underline bright_blue]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Degree", style="cyan")
    table.add_column("Institution", style="yellow")
    table.add_column("Tenure", style="green")
    table.add_column("Notes", style="white")

    for edu in education:
        table.add_row(
            edu.get("degree", "N/A"),
            edu.get("institution", "N/A"),
            edu.get("tenure", "N/A"),
            edu.get("notes", "—"),
        )

    console.print(table)