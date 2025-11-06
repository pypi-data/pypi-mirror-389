"""Main CLI entry point."""

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional

from .commands import info, work_exp, contact, summary, projects, education, skills

app = typer.Typer(
    name="sheikh-huzaif-resume",
    help="A CLI tool to showcase my CV",
    add_completion=False,
    rich_markup_mode="rich",  # Explicitly set rich markup mode
)
console = Console()

# Register commands
app.command(name="info")(info.main)
app.command(name="contact")(contact.main)
app.command(name="summary")(summary.main)
app.command(name="work-exp")(work_exp.main)
app.command(name="projects")(projects.main)
app.command(name="education")(education.main)
app.command(name="skills")(skills.main)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Sheikh Huzaif Resume - An interactive CLI resume

    Run sheikh-huzaif-resume COMMAND to view different sections.
    """
    if ctx.invoked_subcommand is None:
        welcome_text = """[bold cyan]Welcome to Sheikh Huzaif's Resume![/bold cyan]

An interactive command-line resume built with Python.

Run [bold green]sheikh-huzaif-resume COMMAND[/bold green] to explore different sections.

Available commands: info, contact, summary, work-exp, projects, education, skills"""

        console.print(Panel(welcome_text, border_style="cyan", padding=(1, 2)))


def run():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()