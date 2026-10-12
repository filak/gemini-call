import argparse

from .client import call
from .config import GEMINI_MODEL_DEF


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="gemini",
        description="Call Gemini API with prompt + files",
    )
    parser.add_argument("prompt", help="Prompt text")
    parser.add_argument(
        "-f",
        "--file",
        action="append",
        dest="files",
        default=[],
        help="File to attach (repeatable): image, txt, json",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=None,
        help=f"Model, default: {GEMINI_MODEL_DEF}",
    )
    parser.add_argument(
        "-s",
        "--system",
        default=None,
        help="System instruction",
    )
    args = parser.parse_args()
    try:
        print(
            call(
                args.prompt,
                files=args.files,
                model=args.model,
                system=args.system,
            )
        )
    except RuntimeError as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
