# gemini-call

A compact Gemini API wrapper and CLI for sending a prompt and optional files to a Gemini model.

## Setup

1. Copy `.env.example` to `.env`.
2. Add your Gemini API key to `.env`.
3. Install the package and its dependencies.
4. Run the CLI with a prompt and optional files.

## Commands

```bash
uv sync
# PowerShell: Copy-Item .env.example .env
# POSIX shell: cp .env.example .env
uv run --env-file .env gemini "hello"
uv run --env-file .env gemini "Explain this file" -f README.md
```

## Environment variables

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `GEMINI_MODEL` (optional, defaults to `gemini-2.5-flash`)

Do not commit `.env`. The command reads attached text and JSON files as text.
It sends other file types as inline binary data.
