# explain.py

A tiny CLI that streams a plain-English explanation of a source file using
Claude Opus 4.7.

Showcases the `claude-api` skill in action:

- **Opus 4.7** with `claude-opus-4-7`
- **Adaptive thinking** (`thinking: {type: "adaptive"}`) — Claude decides how
  much to reason
- **Effort=high** for intelligence-sensitive code review
- **Prompt caching** on the system prompt — a 5-minute ephemeral breakpoint
  means repeated runs only pay for the changing user content
- **Streaming** via `messages.stream()` so output starts immediately
- **Typed exception handling** for auth, rate-limit, and API errors

## Usage

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python explain.py path/to/file.py
python explain.py src/server.ts "focus on concurrency safety"
```

The trailing stderr line reports token usage including `cache_read` — re-run
within 5 minutes against any file and you'll see the cache_read input tokens
match the system-prompt size.
