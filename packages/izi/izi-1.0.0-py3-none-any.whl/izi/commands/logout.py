"""Logout command"""

import click
from rich.console import Console
from ..config import config

console = Console()


def logout_command():
    """Clear stored credentials"""
    try:
        if not config.is_authenticated():
            console.print("[yellow]You are not authenticated.[/yellow]")
            return

        config.clear_token()
        console.print("[green]✓ Successfully logged out![/green]")
        console.print("[dim]Your credentials have been cleared.[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Failed to logout: {str(e)}[/red]")
        raise click.Abort()
