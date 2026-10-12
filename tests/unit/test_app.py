import pytest

from gemini_call import cli
from gemini_call.config import GEMINI_MODEL_DEF, get_api_key, get_model
from gemini_call.files import load_part, load_parts


def test_get_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert get_api_key() == "test-key"


def test_get_api_key_requires_value(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Missing GEMINI_API_KEY"):
        get_api_key()


def test_get_model_uses_default(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert get_model() == GEMINI_MODEL_DEF


def test_load_part_reads_text_file(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello world\n", encoding="utf-8")
    assert load_part(str(file_path))["text"].startswith("File notes.txt:")


def test_load_parts_returns_empty_for_none():
    assert load_parts([]) == []


def test_cli_passes_arguments_to_call(monkeypatch, capsys):
    monkeypatch.setattr(cli, "call", lambda *args, **kwargs: "result")
    monkeypatch.setattr(
        "sys.argv", ["gemini", "hello", "-f", "note.txt", "-m", "model"]
    )

    assert cli.main() == 0
    assert capsys.readouterr().out == "result\n"
