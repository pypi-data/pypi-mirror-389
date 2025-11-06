"""Work Experience command implementation."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown

from ..data import resume
console = Console()

def main(
        verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed information"
    ),
):
    """Display Work Experience"""
    jobs = resume.get("jobs")

    for job in jobs:
        header = Text(job.get("company", "Unknown Company"), style="bold cyan")
        header.append(f" • {job.get('role', 'Unknown Role')} •", style="bold yellow")
        header.append(f"\n{job.get('tenure', '')} | {job.get('location', '')}", style="dim")

        highlights_list = job.get("highlights", [])
        if highlights_list:
            highlights_md = "\n".join([f"- {h}" for h in highlights_list])
            highlights = Markdown(f"**Highlights:**\n{highlights_md}")
        else:
            highlights = Text("No highlights provided.", style="italic dim")

        console.print(
            Panel.fit(
                highlights,
                title=header,
                border_style="bright_blue",
                padding=(1, 2),
            )
        )
