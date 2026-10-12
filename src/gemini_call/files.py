import json
import mimetypes
import pathlib
from typing import Any, Dict, List

TEXT_SUFFIXES = {".txt", ".md", ".py", ".csv", ".log"}


def load_part(path: str) -> Dict[str, Any]:
    file_path = pathlib.Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if file_path.is_dir():
        raise ValueError(f"Expected file, got directory: {file_path}")

    if file_path.suffix.lower() in TEXT_SUFFIXES:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return {"text": f"File {file_path.name}:\n{text[:20000]}"}

    if file_path.suffix.lower() == ".json":
        payload = json.loads(file_path.read_bytes())
        json_text = json.dumps(payload, indent=2, ensure_ascii=False)[:20000]
        return {"text": f"JSON {file_path.name}:\n{json_text}"}

    mime_type, _ = mimetypes.guess_type(str(file_path))
    return {
        "inline_data": {
            "mime_type": mime_type or "application/octet-stream",
            "data": file_path.read_bytes(),
        }
    }


def load_parts(paths: List[str]) -> List[Dict[str, Any]]:
    return [load_part(path) for path in paths] if paths else []
