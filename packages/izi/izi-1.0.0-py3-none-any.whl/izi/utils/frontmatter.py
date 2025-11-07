"""Frontmatter parsing utilities"""

import frontmatter
from typing import Dict, Any, Tuple


def parse_markdown_file(file_path: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse a markdown file with YAML frontmatter

    Args:
        file_path: Path to the markdown file

    Returns:
        Tuple of (metadata dict, content string)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)

    return dict(post.metadata), post.content


def create_markdown_file(file_path: str, metadata: Dict[str, Any], content: str):
    """
    Create a markdown file with YAML frontmatter

    Args:
        file_path: Path where to save the file
        metadata: Dictionary of metadata for frontmatter
        content: The markdown content
    """
    post = frontmatter.Post(content, **metadata)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))
