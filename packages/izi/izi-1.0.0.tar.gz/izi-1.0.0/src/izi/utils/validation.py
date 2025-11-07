"""Validation utilities for prompts"""

from typing import List, Optional
from ..constants import ERRORS, LIMITS


class ValidationError(Exception):
    """Custom exception for validation errors"""

    pass


def validate_name(name: Optional[str]) -> str:
    """Validate prompt name"""
    if not name or not name.strip():
        raise ValidationError(ERRORS.NAME_REQUIRED)

    if len(name) > LIMITS.MAX_NAME_LENGTH:
        raise ValidationError(ERRORS.NAME_TOO_LONG)

    return name.strip()


def validate_description(description: Optional[str]) -> str:
    """Validate prompt description"""
    if not description or not description.strip():
        raise ValidationError(ERRORS.DESCRIPTION_REQUIRED)

    if len(description) > LIMITS.MAX_DESCRIPTION_LENGTH:
        raise ValidationError(ERRORS.DESCRIPTION_TOO_LONG)

    return description.strip()


def validate_content(content: str) -> str:
    """Validate prompt content"""
    content_size = len(content.encode("utf-8"))

    if content_size > LIMITS.MAX_CONTENT_SIZE:
        raise ValidationError(ERRORS.CONTENT_TOO_LARGE)

    return content


def validate_tags(tags: List[str]) -> List[str]:
    """Validate and clean tags"""
    if not tags:
        return []

    # Clean and filter tags
    cleaned_tags = [tag.strip() for tag in tags if tag.strip()]

    # Check tag count
    if len(cleaned_tags) > LIMITS.MAX_TAGS_COUNT:
        raise ValidationError(f"Too many tags. Maximum {LIMITS.MAX_TAGS_COUNT} tags allowed")

    # Check individual tag length
    for tag in cleaned_tags:
        if len(tag) > LIMITS.MAX_TAG_LENGTH:
            raise ValidationError(f"Tag '{tag}' is too long. Maximum {LIMITS.MAX_TAG_LENGTH} characters")

    return cleaned_tags


def validate_file_extension(file_path: str):
    """Validate that file has .md extension"""
    if not file_path.endswith(".md"):
        raise ValidationError(ERRORS.INVALID_FILE_EXTENSION(file_path))
