# gemini-call

A compact Gemini API wrapper and CLI for sending a prompt and optional files to a Gemini model.

This project uses LLM-AI coding tools.

The current project status is: in development

[![CodeQL](https://github.com/filak/gemini-call/actions/workflows/codeql.yml/badge.svg)](https://github.com/filak/gemini-call/security/code-scanning)

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

```bash
uv sync --upgrade
```

## Setup

Set a Gemini API key as an environment variable: GEMINI_API_KEY

```bash
# CMD: setx /M GEMINI_API_KEY "your-api-key"
# PowerShell: $env:GEMINI_API_KEY = "your-api-key"
# POSIX shell: export GEMINI_API_KEY="your-api-key"
```

## Commands

```bash
uv run gemini --help
```

```bash
usage: gemini [-h] [-f FILES] [-m MODEL] [-s SYSTEM] [-n] [--response-format {text,json}] prompt

Call Gemini API with prompt + files

positional arguments:
  prompt                Prompt text

options:
  -h, --help            show this help message and exit
  -f FILES, --file FILES
                        File to attach (repeatable): html, image (PNG, JPEG, WEBP), json, txt
  -m MODEL, --model MODEL
                        Model, default: gemini-3.8-flash
  -s SYSTEM, --system SYSTEM
                        System instruction
  -n, --include-file-name
                        Include original file names with attached contents
  --response-format {text,json}
                        Output format (default: text); includes token usage
```

Examples:

```bash
uv run gemini "hello"
uv run gemini "Explain this file" -f README.txt
```

## Environment variables

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `GEMINI_MODEL` (optional, defaults to `gemini-3.8-flash`)

The command reads attached text and JSON files as text. It sends other file
types as inline binary data.


## Development

Run the following commands from the repository root.
Install the locked Python dependencies:

```bash
uv sync --locked
```

Testing:

```bash
uv run pytest
```
