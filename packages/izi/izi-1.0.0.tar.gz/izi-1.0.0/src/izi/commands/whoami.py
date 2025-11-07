"""Whoami command"""

import click
from rich.console import Console
from ..api import api
from ..config import config
from ..constants import ERRORS

console = Console()


def whoami_command():
    """Show current user"""
    try:
        # Check authentication
        if not config.is_authenticated():
            console.print(f"[red]{ERRORS.NOT_AUTHENTICATED}[/red]")
            raise click.Abort()

        # Get user info
        with console.status("[cyan]Fetching user info...[/cyan]"):
            user = api.get_current_user()

        # Display user info
        console.print(f"\n[green bold]Authenticated as:[/green bold]")
        console.print(f"[cyan]Username:[/cyan] {user.get('username', 'Unknown')}")
        if user.get('email'):
            console.print(f"[cyan]Email:[/cyan] {user.get('email')}")

    except Exception as e:
        console.print(f"[red]❌ Failed to get user info: {str(e)}[/red]")
        raise click.Abort()
