"""Contact command implementation."""

import typer
from rich.console import Console
from rich.table import Table

from ..data import resume
from ..utils.helpers import safe_get

console = Console()

def main(
        verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed information"
    ),
):
    """Contact Information"""
    contact_info = resume.get("contact")
    if not contact_info:
        console.print("[bold red]Error:[/bold red] No contact information found.")
        raise typer.Exit(code=1)

    table = Table(title="📇 Contact Information", show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold cyan]Name[/bold cyan]", safe_get(contact_info, "name"))
    table.add_row("[bold cyan]Email[/bold cyan]", safe_get(contact_info, "email"))
    table.add_row("[bold cyan]Phone[/bold cyan]", safe_get(contact_info, "phone"))
    table.add_row("[bold cyan]LinkedIn[/bold cyan]", safe_get(contact_info, "linkedin"))
    table.add_row("[bold cyan]GitHub[/bold cyan]", safe_get(contact_info, "github"))

    console.print(table)
        
