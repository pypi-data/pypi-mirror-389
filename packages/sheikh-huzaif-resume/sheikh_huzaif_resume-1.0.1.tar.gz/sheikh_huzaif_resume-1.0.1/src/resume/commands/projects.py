"""Projects command implementation."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import questionary

from ..data import resume

console = Console()


def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed information"
    ),
):
    """Projects Implemented"""
    projects = resume.get("projects")
    if not projects:
        console.print("[bold red]No projects found.[/bold red]")
        return

    console.print("\n🚀 [bold underline bright_blue]Projects[/bold underline bright_blue]\n")

    for proj in projects:
        name = proj.get("name", "Unnamed Project")
        role = proj.get("role", "N/A")
        tenure = proj.get("tenure", "N/A")
        highlights = proj.get("highlights", []) or []
        link = proj.get("link", "")

        grid = Table.grid(padding=(0, 1))
        grid.add_column(justify="right", style="bold yellow", no_wrap=True)
        grid.add_column(ratio=1)

        grid.add_row("Role:", role)
        grid.add_row("Tenure:", tenure)

        if highlights:
            grid.add_row("Highlights:", "\n".join(f"• {h}" for h in highlights))
        else:
            grid.add_row("Highlights:", "—")

        if link:
            grid.add_row("Link:", f"[link={link}]{link}[/link]")
        else:
            grid.add_row("Link:", "—")

        panel = Panel(
            grid,
            title=f"[bold cyan]{name}[/bold cyan]",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )

        console.print(panel)