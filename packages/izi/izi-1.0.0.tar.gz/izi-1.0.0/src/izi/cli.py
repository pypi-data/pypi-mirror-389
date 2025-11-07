#!/usr/bin/env python3
"""Main CLI entry point for Gitizi"""

import click
from rich.console import Console
from . import __version__
from .constants import CAT_ASCII
from .commands.auth import auth_command
from .commands.search import search_command
from .commands.create import create_command
from .commands.push import push_command
from .commands.clone import clone_command
from .commands.list import list_command
from .commands.whoami import whoami_command
from .commands.logout import logout_command
from .commands.config import config_command

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """Official CLI tool for managing prompts on gitizi.com"""
    console.print(f"[cyan]{CAT_ASCII}[/cyan]")
    console.print("[bold cyan]Gitizi CLI - Your friendly prompt manager[/bold cyan]\n")


@cli.command()
@click.option("-t", "--token", help="API token")
def auth(token):
    """Authenticate with gitizi.com"""
    auth_command(token)


@cli.command()
@click.argument("query")
@click.option("-l", "--limit", default=10, help="Limit results (default: 10)")
def search(query, limit):
    """Search for prompts on gitizi.com"""
    search_command(query, limit)


@cli.command()
@click.argument("file")
@click.option("-n", "--name", help="Prompt name")
@click.option("-d", "--description", help="Prompt description")
@click.option("--tags", help="Comma-separated tags")
def create(file, name, description, tags):
    """Create a new prompt from markdown file"""
    create_command(file, name, description, tags)


@cli.command()
@click.argument("file")
@click.option("--id", "prompt_id", help="Prompt ID (for updates)")
def push(file, prompt_id):
    """Push a prompt to gitizi.com"""
    push_command(file, prompt_id)


@cli.command()
@click.argument("prompt_id")
@click.option("-o", "--output", default="./prompt.md", help="Output file path")
def clone(prompt_id, output):
    """Clone an existing prompt"""
    clone_command(prompt_id, output)


@cli.command()
@click.option("-l", "--limit", default=10, help="Limit results (default: 10)")
def list(limit):
    """List your prompts"""
    list_command(limit)


@cli.command()
def whoami():
    """Show current user"""
    whoami_command()


@cli.command()
def logout():
    """Clear stored credentials"""
    logout_command()


@cli.command()
@click.argument("action", type=click.Choice(["get", "set", "list"]))
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(action, key, value):
    """Manage configuration"""
    config_command(action, key, value)


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
