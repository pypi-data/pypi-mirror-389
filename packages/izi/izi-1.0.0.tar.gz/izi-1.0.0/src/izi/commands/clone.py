"""Clone command"""

import click
from rich.console import Console
from ..api import api
from ..constants import ERRORS, MESSAGES, TIPS, URLS
from ..utils.frontmatter import create_markdown_file

console = Console()


def clone_command(prompt_id: str, output: str = "./prompt.md"):
    """Clone an existing prompt"""
    try:
        # Fetch the prompt
        with console.status(f"[cyan]Fetching prompt {prompt_id}...[/cyan]"):
            prompt = api.get_prompt(prompt_id)

        # Prepare metadata
        metadata = {
            "name": prompt.name,
            "description": prompt.description,
            "tags": prompt.tags,
        }

        # Save to file
        create_markdown_file(output, metadata, prompt.content)

        # Success message
        console.print(f"\n[green bold]{MESSAGES.PROMPT_CLONED}[/green bold]")
        console.print(f"[green]✓ Saved to: {output}[/green]")
        console.print(f"[dim]View online: {URLS.PROMPTS(prompt_id)}[/dim]")
        console.print(f"\n[cyan]{TIPS.PUSH_UPDATE(output, prompt_id)}[/cyan]")

    except Exception as e:
        console.print(f"[red]❌ {ERRORS.CLONE_FAILED}: {str(e)}[/red]")
        raise click.Abort()
