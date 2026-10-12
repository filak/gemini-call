from __future__ import annotations

from typing import Optional, Sequence

from google import genai
from google.genai import types
from google.genai.errors import APIError

from .config import get_api_key, get_model
from .files import load_parts

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_api_key())
    return _client


def call(
    prompt: str,
    files: Optional[Sequence[str]] = None,
    model: Optional[str] = None,
    system: Optional[str] = None,
) -> str:
    contents = [prompt, *load_parts(list(files or []))]
    config = None
    if system:
        config = types.GenerateContentConfig(system_instruction=system)

    try:
        response = get_client().models.generate_content(
            model=model or get_model(),
            contents=contents,
            config=config,
        )
        return response.text or ""
    except APIError as exc:
        raise RuntimeError(f"Gemini API Error: {exc}") from exc
