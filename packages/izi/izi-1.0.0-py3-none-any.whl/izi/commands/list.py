"""List command"""

import click
from rich.console import Console
from rich.table import Table
from ..api import api
from ..config import config
from ..constants import ERRORS

console = Console()


def list_command(limit: int = 10):
    """List your prompts"""
    try:
        # Check authentication
        if not config.is_authenticated():
            console.print(f"[red]{ERRORS.NOT_AUTHENTICATED}[/red]")
            raise click.Abort()

        # Fetch user's prompts
        with console.status("[cyan]Fetching your prompts...[/cyan]"):
            prompts = api.list_user_prompts()

        # Limit results
        prompts = prompts[:limit]

        if not prompts:
            console.print("\n[yellow]No prompts found.[/yellow]")
            console.print("[dim]Create your first prompt with: izi push <file>[/dim]")
            return

        # Display results in a table
        table = Table(title=f"Your Prompts ({len(prompts)} shown)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        table.add_column("Tags", style="magenta")

        for prompt in prompts:
            tags_str = ", ".join(prompt.tags) if prompt.tags else ""
            table.add_row(
                prompt.id[:8] + "...",
                prompt.name[:30] + "..." if len(prompt.name) > 30 else prompt.name,
                prompt.description[:50] + "..." if len(prompt.description) > 50 else prompt.description,
                tags_str[:30] + "..." if len(tags_str) > 30 else tags_str,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Failed to list prompts: {str(e)}[/red]")
        raise click.Abort()
