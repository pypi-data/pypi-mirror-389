"""Skills command implementation."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import textwrap

from ..data import resume
from ..utils.helpers import format_category_name

console = Console()

def main(
        verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed information"
    ),
):
    """
    Technical Skills
    """
    skills = resume.get("skills")
    if not skills:
        console.print("[bold red]No skills data found.[/bold red]")
        return

    console.print("\n🧠 [bold underline bright_blue]Technical Skills[/bold underline bright_blue]\n")

    for category, items in skills.items():
        title = format_category_name(category)
        formatted_items = ", ".join(items)
        panel = Panel(
            formatted_items,
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="bright_blue",
            padding=(1, 2),
            expand=False,
        )
        console.print(panel)