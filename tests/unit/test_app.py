import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from google.genai import types
from google.genai.errors import APIError

from gemini_call import cli, client
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
    mocked_call = Mock(return_value="Tokens: total_token_count=12\nresult")
    monkeypatch.setattr(cli, "call", mocked_call)
    monkeypatch.setattr(
        "sys.argv", ["gemini", "hello", "-f", "note.txt", "-m", "model"]
    )

    assert cli.main() == 0
    assert capsys.readouterr().out == "Tokens: total_token_count=12\nresult\n"
    mocked_call.assert_called_once_with(
        "hello",
        files=["note.txt"],
        model="model",
        system=None,
        include_file_name=False,
        response_format="text",
    )


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


@pytest.fixture
def generate_content(monkeypatch):
    generate = Mock(
        return_value=types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        parts=[types.Part(text="Příliš žluťoučký\nresult")]
                    )
                )
            ],
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=10,
                candidates_token_count=20,
                thoughts_token_count=5,
                cached_content_token_count=4,
                tool_use_prompt_token_count=2,
                total_token_count=37,
            ),
        )
    )
    monkeypatch.setattr(
        client,
        "get_client",
        lambda: SimpleNamespace(models=SimpleNamespace(generate_content=generate)),
    )
    return generate


def test_call_json_preserves_usage_and_request(generate_content, monkeypatch):
    load = Mock(return_value=[{"text": "attached"}])
    monkeypatch.setattr(client, "load_parts", load)
    result = client.call(
        "hello",
        files=["notes.txt"],
        model="test-model",
        system="instruction",
        include_file_name=True,
        response_format="json",
    )
    assert result == {
        "response": "Příliš žluťoučký\nresult",
        "usage": {
            "prompt_token_count": 10,
            "candidates_token_count": 20,
            "total_token_count": 37,
            "thoughts_token_count": 5,
            "cached_content_token_count": 4,
            "tool_use_prompt_token_count": 2,
        },
    }
    assert json.loads(json.dumps(result)) == result
    load.assert_called_once_with(["notes.txt"], include_file_name=True)
    request = generate_content.call_args.kwargs
    assert request["model"] == "test-model"
    assert request["contents"] == ["hello", {"text": "attached"}]
    assert request["config"].system_instruction == "instruction"
    assert request["config"].response_mime_type is None


def test_call_text_starts_with_usage(generate_content):
    result = client.call("hello")
    header, text = result.split("\n", 1)
    assert header.startswith("Tokens: ")
    assert "total_token_count=37" in header
    assert "thoughts_token_count=5" in header
    assert text == "Příliš žluťoučký\nresult"


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        types.GenerateContentResponseUsageMetadata(
            prompt_token_count=0,
            total_token_count=0,
        ),
    ],
)
def test_call_handles_missing_usage_and_empty_text(generate_content, metadata):
    generate_content.return_value = types.GenerateContentResponse(
        usage_metadata=metadata,
    )
    result = client.call("hello", response_format="json")
    assert result["response"] == ""
    assert result["usage"]["total_token_count"] == (0 if metadata else None)
    assert result["usage"]["candidates_token_count"] is None
    assert "candidates_token_count=unavailable" in client.call("hello")


def test_call_rejects_invalid_format_before_request(generate_content):
    with pytest.raises(ValueError, match="response_format"):
        client.call("hello", response_format="xml")
    generate_content.assert_not_called()


def test_call_wraps_api_errors(generate_content):
    generate_content.side_effect = APIError(500, {"message": "failed"})
    with pytest.raises(RuntimeError, match="Gemini API Error"):
        client.call("hello", response_format="json")


def test_cli_json_is_one_document(monkeypatch, capsys):
    result = {
        "response": "Příliš žluťoučký\nresult",
        "usage": {"total_token_count": 37},
    }
    mocked_call = Mock(return_value=result)
    monkeypatch.setattr(cli, "call", mocked_call)
    monkeypatch.setattr("sys.argv", ["gemini", "hello", "--response-format", "json"])
    assert cli.main() == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == result
    assert "Příliš" in captured.out
    assert captured.err == ""
    assert mocked_call.call_args.kwargs["response_format"] == "json"


def test_cli_invalid_format_does_not_call_api(monkeypatch, capsys):
    mocked_call = Mock()
    monkeypatch.setattr(cli, "call", mocked_call)
    monkeypatch.setattr("sys.argv", ["gemini", "hello", "--response-format", "xml"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    mocked_call.assert_not_called()
    assert capsys.readouterr().out == ""


def test_cli_error_stays_on_stderr(monkeypatch, capsys):
    monkeypatch.setattr(cli, "call", Mock(side_effect=RuntimeError("failed")))
    monkeypatch.setattr("sys.argv", ["gemini", "hello", "--response-format", "json"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "failed" in captured.err


@pytest.mark.parametrize("response_format", ["text", "json"])
def test_html_response_round_trip(generate_content, tmp_path, response_format):
    prompt = "Clean and normalize the attached HTML using the given rules."
    system = "Return only valid cleaned HTML, without Markdown fences."
    source = "<h1>Článek</h1><p>infor-<br>mation &amp; text</p>"
    cleaned = '<h1>Článek</h1>\n<p class="body">information &amp; text</p>'
    attachment = tmp_path / "input.html"
    attachment.write_text(source, encoding="utf-8")
    generate_content.return_value.candidates[0].content.parts = [
        types.Part(text=cleaned)
    ]

    result = client.call(
        prompt,
        files=[str(attachment)],
        system=system,
        response_format=response_format,
    )

    request = generate_content.call_args.kwargs
    assert request["contents"] == [prompt, {"text": source}]
    assert request["config"].system_instruction == system
    if response_format == "json":
        decoded = json.loads(json.dumps(result))
        assert decoded["response"] == cleaned
        assert decoded["usage"]["total_token_count"] == 37
    else:
        header, body = result.split("\n", 1)
        assert header.startswith("Tokens: ")
        assert "total_token_count=37" in header
        assert body == cleaned


@pytest.mark.parametrize("response_format", ["text", "json"])
def test_cli_html_response_round_trip(
    generate_content, tmp_path, monkeypatch, capsys, response_format
):
    cleaned = '<h1>Článek</h1>\n<p title="Example">Text &amp; more.</p>'
    attachment = tmp_path / "input.html"
    attachment.write_text("<h1>Článek</h1><p>Text</p>", encoding="utf-8")
    generate_content.return_value.candidates[0].content.parts = [
        types.Part(text=cleaned)
    ]
    monkeypatch.setattr(
        "sys.argv",
        [
            "gemini",
            "Clean HTML",
            "-f",
            str(attachment),
            "--system",
            "Return only HTML",
            "--response-format",
            response_format,
        ],
    )

    assert cli.main() == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    if response_format == "json":
        result = json.loads(captured.out)
        assert result["response"] == cleaned
        assert result["usage"]["total_token_count"] == 37
    else:
        header, body = captured.out.split("\n", 1)
        assert header.startswith("Tokens: ")
        assert body == cleaned + "\n"


@pytest.mark.parametrize("suffix", [".html", ".htm", ".HTML", ".HTM"])
@pytest.mark.parametrize("include_file_name", [False, True])
def test_load_html_as_complete_text(tmp_path, suffix, include_file_name):
    html = "<h1>Článek</h1><p>" + "Žluťoučký &amp; text. " * 1500 + "</p>END"
    attachment = tmp_path / ("article" + suffix)
    attachment.write_text(html, encoding="utf-8")
    result = load_part(str(attachment), include_file_name=include_file_name)
    prefix = f"File {attachment.name}:\n" if include_file_name else ""
    assert result == [{"text": prefix + html}]


@pytest.mark.parametrize("include_file_name", [False, True])
def test_load_text_does_not_truncate(tmp_path, include_file_name):
    text = "x" * 20000 + "END"
    attachment = tmp_path / "long.txt"
    attachment.write_text(text, encoding="utf-8")
    prefix = "File long.txt:\n" if include_file_name else ""
    assert load_part(str(attachment), include_file_name=include_file_name) == [
        {"text": prefix + text}
    ]


@pytest.mark.parametrize("include_file_name", [False, True])
def test_load_json_does_not_truncate(tmp_path, include_file_name):
    payload = {"text": "Ž" * 20000 + "END"}
    attachment = tmp_path / "long.json"
    attachment.write_text(json.dumps(payload), encoding="utf-8")
    text = load_part(str(attachment), include_file_name=include_file_name)[0]["text"]
    if include_file_name:
        prefix, text = text.split("\n", 1)
        assert prefix == "JSON long.json:"
    assert json.loads(text) == payload
