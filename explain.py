#!/usr/bin/env python3
"""Stream a plain-English explanation of a source file using Claude Opus 4.7.

Usage:
    export ANTHROPIC_API_KEY=...
    python explain.py path/to/file.py
    python explain.py path/to/file.py "focus on the error handling"

You can also just double-click this file — it will prompt for a path.
"""

import os
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("error: the 'anthropic' package is not installed.", file=sys.stderr)
    print("       run: pip install -U anthropic", file=sys.stderr)
    input("\nPress Enter to exit...")
    sys.exit(1)


def _is_double_click() -> bool:
    """Best-effort detection of Windows double-click launch (no args, no TTY parent)."""
    return os.name == "nt" and len(sys.argv) < 2


def _pause_if_double_click() -> None:
    if _is_double_click():
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass

SYSTEM_PROMPT = """You are an expert code reviewer with deep experience across
languages, frameworks, and architectures. When given a source file, produce:

1. **One-line summary** — what this file does in plain English.
2. **Structure** — the key functions/classes and how they connect.
3. **Notable choices** — anything clever, unusual, or worth flagging.
4. **Risks** — bugs, edge cases, or maintainability concerns. Be specific.

Be concrete. Reference identifiers by name. Skip restating obvious code.
"""


def main() -> int:
    if len(sys.argv) >= 2:
        path = Path(sys.argv[1])
        focus = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Interactive fallback (e.g. Windows double-click)
        print("Stream a plain-English explanation of a source file.\n")
        raw = input("File path: ").strip().strip('"').strip("'")
        if not raw:
            print("no path given", file=sys.stderr)
            return 2
        path = Path(raw)
        focus = input("Extra focus (optional, press Enter to skip): ").strip() or None

    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
        return 1

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        print(
            "       set it first, e.g. (Windows):\n"
            '         setx ANTHROPIC_API_KEY "sk-ant-..."\n'
            "       then open a NEW terminal and re-run.",
            file=sys.stderr,
        )
        return 1

    source = path.read_text(errors="replace")
    user_prompt = f"File: `{path}`\n\n```\n{source}\n```"
    if focus:
        user_prompt += f"\n\nExtra focus: {focus}"

    client = anthropic.Anthropic()

    try:
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            final = stream.get_final_message()

        print()
        u = final.usage
        print(
            f"\n[input={u.input_tokens} output={u.output_tokens} "
            f"cache_write={u.cache_creation_input_tokens} "
            f"cache_read={u.cache_read_input_tokens}]",
            file=sys.stderr,
        )
        return 0

    except anthropic.AuthenticationError:
        print("error: invalid or missing ANTHROPIC_API_KEY", file=sys.stderr)
        return 1
    except anthropic.RateLimitError:
        print("error: rate limited — try again in a moment", file=sys.stderr)
        return 1
    except anthropic.APIStatusError as e:
        print(f"error: API returned {e.status_code}: {e.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        code = 130
    except Exception as e:
        print(f"\nunexpected error: {type(e).__name__}: {e}", file=sys.stderr)
        code = 1
    _pause_if_double_click()
    sys.exit(code)
