"""Create command"""

import os
import click
from rich.console import Console
from ..constants import ERRORS, TIPS
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


def create_command(file: str, name: str = None, description: str = None, tags: str = None):
    """Create a new prompt from markdown file (validates locally)"""
    try:
        # Check if file exists
        if not os.path.exists(file):
            console.print(f"[red]{ERRORS.FILE_NOT_FOUND(file)}[/red]")
            raise click.Abort()

        # Validate file extension
        validate_file_extension(file)

        # Parse the markdown file
        metadata, content = parse_markdown_file(file)

        # Override with command-line options if provided
        prompt_name = name or metadata.get("name")
        prompt_description = description or metadata.get("description")
        prompt_tags = []

        if tags:
            prompt_tags = [t.strip() for t in tags.split(",")]
        elif "tags" in metadata:
            prompt_tags = metadata["tags"] if isinstance(metadata["tags"], list) else []

        # Validate all fields
        prompt_name = validate_name(prompt_name)
        prompt_description = validate_description(prompt_description)
        content = validate_content(content)
        prompt_tags = validate_tags(prompt_tags)

        # Show validation success
        console.print("\n[green bold]✓ Prompt validation successful![/green bold]")
        console.print(f"[cyan]Name:[/cyan] {prompt_name}")
        console.print(f"[cyan]Description:[/cyan] {prompt_description}")
        console.print(f"[cyan]Tags:[/cyan] {', '.join(prompt_tags) if prompt_tags else 'None'}")
        console.print(f"[cyan]Content size:[/cyan] {len(content)} characters")

        console.print(f"\n[dim]{TIPS.PUSH(file)}[/dim]")

    except ValidationError as e:
        console.print(f"[red]❌ Validation failed: {str(e)}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise click.Abort()
