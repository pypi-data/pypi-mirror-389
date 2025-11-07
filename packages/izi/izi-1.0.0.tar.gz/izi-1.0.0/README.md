# Gitizi CLI (izi)

The official Python command-line interface for [gitizi.com](https://gitizi.com) - manage your AI prompts like a pro!

## Features

- **Authentication** - Secure token-based authentication with gitizi.com
- **Search Prompts** - Find prompts from the community
- **Create Prompts** - Create prompts from markdown files with frontmatter
- **Push Prompts** - Upload and update prompts to gitizi.com
- **Clone Prompts** - Download existing prompts to edit locally
- **Beautiful Output** - Rich terminal experience with tables and colors

## Installation

Install from PyPI:

```bash
pip install izi
```

Or install from source:

```bash
git clone https://github.com/cpaka/izi-py.git
cd izi-py
pip install -e .
```

## Quick Start

### 1. Authenticate

```bash
izi auth
```

Or provide token directly:

```bash
izi auth --token YOUR_API_TOKEN
```

Get your API token from: https://gitizi.com/settings/tokens

### 2. Search for Prompts

```bash
izi search "code review"
izi search "typescript" --limit 20
```

### 3. Clone an Existing Prompt

```bash
izi clone abc123 -o my-prompt.md
```

### 4. Create a New Prompt

Create a markdown file with frontmatter:

```markdown
---
name: My Awesome Prompt
description: A prompt that does amazing things
tags: [coding, typescript, assistant]
---

You are an expert TypeScript developer...
```

Then validate it:

```bash
izi create my-prompt.md
```

### 5. Push Your Prompt

```bash
izi push my-prompt.md
```

Update an existing prompt:

```bash
izi push my-prompt.md --id abc123
```

## Commands

### `izi auth [options]`

Authenticate with gitizi.com

**Options:**
- `-t, --token <token>` - API token

### `izi search <query> [options]`

Search for prompts on gitizi.com

**Arguments:**
- `query` - Search query

**Options:**
- `-l, --limit <number>` - Limit results (default: 10)

### `izi create <file> [options]`

Create a new prompt from markdown file

**Arguments:**
- `file` - Markdown file path

**Options:**
- `-n, --name <name>` - Prompt name
- `-d, --description <desc>` - Prompt description
- `--tags <tags>` - Comma-separated tags

### `izi push <file> [options]`

Push a prompt to gitizi.com

**Arguments:**
- `file` - Markdown file path

**Options:**
- `--id <id>` - Prompt ID (for updates)

### `izi clone <prompt-id> [options]`

Clone an existing prompt

**Arguments:**
- `prompt-id` - Prompt ID to clone

**Options:**
- `-o, --output <path>` - Output file path (default: ./prompt.md)

### `izi list [options]`

List your prompts

**Options:**
- `-l, --limit <number>` - Limit results (default: 10)

### `izi whoami`

Show current user

### `izi logout`

Clear stored credentials

### `izi config <action> [key] [value]`

Manage configuration

**Actions:**
- `get` - Get a configuration value
- `set` - Set a configuration value
- `list` - List all configuration

## Prompt Format

Prompts should be markdown files with YAML frontmatter:

```markdown
---
name: Prompt Name
description: Brief description of what this prompt does
tags: [tag1, tag2, tag3]
---

Your actual prompt content goes here...
```

## Configuration

Configuration is stored in:
- **Linux/Mac:** `~/.config/izi/config.json`
- **Windows:** `%APPDATA%\izi\config.json`

## Development

```bash
# Clone the repository
git clone https://github.com/cpaka/izi-py.git
cd izi-py

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Type check
mypy src/
```

## Requirements

- Python 3.8 or higher
- pip

## License

MIT

## Support

- Website: https://gitizi.com
- Issues: https://github.com/cpaka/izi-py/issues
- Email: support@gitizi.com

---

Made with love by the Gitizi team
