"""Search command"""

import click
from rich.console import Console
from rich.table import Table
from ..api import api
from ..config import config
from ..constants import ERRORS, MESSAGES, TIPS, URLS

console = Console()


def search_command(query: str, limit: int = 10):
    """Search for prompts on gitizi.com"""
    try:
        # Search prompts
        with console.status(f"[cyan]Searching for '{query}'...[/cyan]"):
            result = api.search_prompts(query, limit)

        # Check if any prompts found
        if not result.prompts:
            console.print(f"[yellow]{MESSAGES.NO_PROMPTS_FOUND}[/yellow]")
            console.print(f"[dim]{TIPS.CLONE_GENERAL}[/dim]")
            return

        # Display results in a table
        table = Table(title=f"Search Results: {result.total} prompts found")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        table.add_column("Tags", style="magenta")
        table.add_column("Author", style="yellow")

        for prompt in result.prompts:
            tags_str = ", ".join(prompt.tags) if prompt.tags else ""
            table.add_row(
                prompt.id[:8] + "...",
                prompt.name[:30] + "..." if len(prompt.name) > 30 else prompt.name,
                prompt.description[:50] + "..." if len(prompt.description) > 50 else prompt.description,
                tags_str[:30] + "..." if len(tags_str) > 30 else tags_str,
                prompt.author
            )

        console.print(table)
        console.print(f"\n[dim]{TIPS.CLONE_GENERAL}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ {ERRORS.SEARCH_FAILED}: {str(e)}[/red]")
        raise click.Abort()
