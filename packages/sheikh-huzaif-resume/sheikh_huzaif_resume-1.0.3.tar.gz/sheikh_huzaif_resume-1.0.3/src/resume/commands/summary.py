"""Summary command implementation."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import textwrap

from ..data import resume
from ..utils.helpers import format_text

console = Console()

def main(
        verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show detailed information"
    ),
):
    """
    Professional Summary
    """
    summary = resume.get("summary")
    if not summary:
        console.print("[bold red]No summary provided.[/bold red]")
        return

    clean_summary = format_text(summary)
    wrapped = textwrap.fill(clean_summary, width=80)

    styled_text = Text(wrapped, justify="left")
    styled_text.stylize("italic cyan", 0, len(wrapped))

    panel = Panel(
        styled_text,
        title="💼 Professional Summary",
        border_style="bright_blue",
        padding=(1, 2),
        expand=False,
    )
    console.print(panel)
