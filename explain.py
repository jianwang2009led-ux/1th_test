#!/usr/bin/env python3
"""Stream a plain-English explanation of a source file using Claude Opus 4.7.

Usage:
    export ANTHROPIC_API_KEY=...
    python explain.py path/to/file.py
    python explain.py path/to/file.py "focus on the error handling"
"""

import sys
from pathlib import Path

import anthropic

SYSTEM_PROMPT = """You are an expert code reviewer with deep experience across
languages, frameworks, and architectures. When given a source file, produce:

1. **One-line summary** — what this file does in plain English.
2. **Structure** — the key functions/classes and how they connect.
3. **Notable choices** — anything clever, unusual, or worth flagging.
4. **Risks** — bugs, edge cases, or maintainability concerns. Be specific.

Be concrete. Reference identifiers by name. Skip restating obvious code.
"""


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    focus = sys.argv[2] if len(sys.argv) > 2 else None

    if not path.is_file():
        print(f"error: {path} is not a file", file=sys.stderr)
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
    sys.exit(main())
