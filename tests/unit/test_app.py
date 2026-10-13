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

    # Passing include_file_name=True ensures "File notes.txt:" header is present
    result = load_part(str(file_path), include_file_name=True)

    # Access the first element since load_part returns a list
    assert result[0]["text"].startswith("File notes.txt:")


def test_load_part_default_omits_filename(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello world\n", encoding="utf-8")

    result = load_part(str(file_path))
    assert result[0]["text"] == "hello world\n"


def test_load_parts_returns_empty_for_none():
    assert load_parts([]) == []


def test_cli_passes_arguments_to_call(monkeypatch, capsys):
    monkeypatch.setattr(cli, "call", lambda *args, **kwargs: "result")
    monkeypatch.setattr(
        "sys.argv", ["gemini", "hello", "-f", "note.txt", "-m", "model"]
    )

    assert cli.main() == 0
    assert capsys.readouterr().out == "result\n"


def test_load_part_unsupported_extension(tmp_path):
    # Test a completely unsupported extension (e.g., .pdf)
    unsupported_file = tmp_path / "document.pdf"
    unsupported_file.write_text("dummy content", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file format '.pdf'"):
        load_part(str(unsupported_file))


def test_load_part_mismatched_extension_png(tmp_path):
    # A text file saved with a .png extension will be treated as an image
    # by extension validation, loading as binary inline_data
    fake_png = tmp_path / "fake_image.png"
    fake_png.write_text("this is plain text content", encoding="utf-8")

    result = load_part(str(fake_png))

    # Expect inline_data payload because of .png extension
    assert len(result) == 1
    assert "inline_data" in result[0]
    assert result[0]["inline_data"]["mime_type"] == "image/png"
    assert result[0]["inline_data"]["data"] == b"this is plain text content"
