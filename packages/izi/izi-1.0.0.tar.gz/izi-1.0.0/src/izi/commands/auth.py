"""Authentication command"""

import click
from rich.console import Console
from rich.prompt import Prompt
from ..api import api
from ..config import config
from ..constants import ERRORS, MESSAGES, TIPS

console = Console()


def auth_command(token: str = None):
    """Authenticate with gitizi.com"""
    try:
        # Check if already authenticated
        if config.is_authenticated() and not token:
            reauth = Prompt.ask(
                MESSAGES.REAUTH_PROMPT,
                choices=["y", "n"],
                default="n"
            )
            if reauth.lower() != "y":
                console.print(f"[green]{MESSAGES.USING_EXISTING_AUTH}[/green]")
                return

        # Get token if not provided
        if not token:
            console.print("[cyan]Get your API token from:[/cyan]")
            console.print(f"[blue]{TIPS.GET_TOKEN()[1]}[/blue]")
            console.print(f"[blue]{TIPS.GET_TOKEN()[2]}[/blue]\n")

            token = Prompt.ask("[cyan]Enter your API token[/cyan]", password=True)

        if not token or not token.strip():
            console.print(f"[red]{ERRORS.TOKEN_EMPTY}[/red]")
            return

        # Verify token with API
        with console.status("[cyan]Verifying token...[/cyan]"):
            result = api.authenticate(token.strip())

        # Save token
        config.set_token(token.strip())

        # Success message
        console.print(f"\n[green bold]{MESSAGES.AUTH_SUCCESS}[/green bold]")
        console.print(f"[green]{MESSAGES.WELCOME(result.get('username', 'User'))}[/green]")
        console.print(f"[dim]{MESSAGES.TOKEN_SAVED}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ {ERRORS.AUTHENTICATION_FAILED}: {str(e)}[/red]")
        raise click.Abort()
