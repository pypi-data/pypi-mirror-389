"""Push command"""

import os
import click
from rich.console import Console
from ..api import api
from ..config import config
from ..constants import ERRORS, MESSAGES, TIPS, URLS
from ..utils.frontmatter import parse_markdown_file
from ..utils.validation import (
    validate_name,
    validate_description,
    validate_content,
    validate_tags,
    validate_file_extension,
    ValidationError,
)

console = Console()


def push_command(file: str, prompt_id: str = None):
    """Push a prompt to gitizi.com"""
    try:
        # Check authentication
        if not config.is_authenticated():
            console.print(f"[red]{ERRORS.NOT_AUTHENTICATED}[/red]")
            raise click.Abort()

        # Check if file exists
        if not os.path.exists(file):
            console.print(f"[red]{ERRORS.FILE_NOT_FOUND(file)}[/red]")
            raise click.Abort()

        # Validate file extension
        validate_file_extension(file)

        # Parse the markdown file
        metadata, content = parse_markdown_file(file)

        # Extract and validate fields
        prompt_name = validate_name(metadata.get("name"))
        prompt_description = validate_description(metadata.get("description"))
        content = validate_content(content)
        prompt_tags = validate_tags(metadata.get("tags", []))

        # Push to API
        if prompt_id:
            # Update existing prompt
            with console.status(f"[cyan]Updating prompt {prompt_id}...[/cyan]"):
                result = api.update_prompt(
                    prompt_id, prompt_name, prompt_description, content, prompt_tags
                )

            console.print(f"\n[green bold]{MESSAGES.PROMPT_UPDATED}[/green bold]")
            console.print(f"[green]✓ Prompt ID: {result.id}[/green]")
            console.print(f"[dim]View online: {URLS.PROMPTS(result.id)}[/dim]")
            console.print(f"\n[cyan]{TIPS.CLONE(result.id)}[/cyan]")

        else:
            # Create new prompt
            with console.status("[cyan]Pushing prompt...[/cyan]"):
                result = api.create_prompt(prompt_name, prompt_description, content, prompt_tags)

            console.print(f"\n[green bold]{MESSAGES.PROMPT_PUSHED}[/green bold]")
            console.print(f"[green]✓ Prompt ID: {result.id}[/green]")
            console.print(f"[dim]View online: {URLS.PROMPTS(result.id)}[/dim]")
            console.print(f"\n[cyan]{TIPS.CLONE(result.id)}[/cyan]")

    except ValidationError as e:
        console.print(f"[red]❌ Validation failed: {str(e)}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ {ERRORS.PUSH_FAILED}: {str(e)}[/red]")
        raise click.Abort()
