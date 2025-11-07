"""Config command"""

import click
from rich.console import Console
from rich.table import Table
from ..config import config

console = Console()


def config_command(action: str, key: str = None, value: str = None):
    """Manage configuration"""
    try:
        if action == "list":
            # List all configuration
            all_config = config.list_all()

            if not all_config:
                console.print("[yellow]No configuration found.[/yellow]")
                return

            table = Table(title="Configuration")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")

            for k, v in all_config.items():
                # Hide sensitive values
                if k == "token":
                    v = "***" + str(v)[-4:] if v else ""
                table.add_row(k, str(v))

            console.print(table)

        elif action == "get":
            if not key:
                console.print("[red]❌ Key is required for 'get' action[/red]")
                raise click.Abort()

            value = config.get(key)
            if value is None:
                console.print(f"[yellow]Key '{key}' not found.[/yellow]")
            else:
                # Hide sensitive values
                if key == "token":
                    value = "***" + str(value)[-4:]
                console.print(f"[cyan]{key}:[/cyan] {value}")

        elif action == "set":
            if not key or value is None:
                console.print("[red]❌ Both key and value are required for 'set' action[/red]")
                raise click.Abort()

            config.set(key, value)
            console.print(f"[green]✓ Set {key} = {value}[/green]")

        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("[dim]Available actions: get, set, list[/dim]")
            raise click.Abort()

    except Exception as e:
        console.print(f"[red]❌ Config error: {str(e)}[/red]")
        raise click.Abort()
