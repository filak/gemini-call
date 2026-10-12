# gemini-call

A compact Gemini API wrapper and CLI for sending a prompt and optional files to a Gemini model.

## Install

Use Python 3.12 or later and [uv](https://docs.astral.sh/uv/).

Install the CLI from a source checkout:

```bash
uv tool install .
```

For development, create the project environment instead:

```bash
uv sync
```

## Setup

1. Set a Gemini API key as an environment variable.
2. Run the CLI with a prompt and optional files.

## Commands

```bash
uv sync
# PowerShell: $env:GEMINI_API_KEY = "your-api-key"
# POSIX shell: export GEMINI_API_KEY="your-api-key"
uv run gemini --help
uv run gemini "hello"
uv run gemini "Explain this file" -f README.md
```

## Environment variables

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `GEMINI_MODEL` (optional, defaults to `gemini-3.8-flash`)

The command reads attached text and JSON files as text. It sends other file
types as inline binary data.
