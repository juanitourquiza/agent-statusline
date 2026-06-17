# Installation

## macOS / Linux

```bash
git clone https://github.com/juanitourquiza/agent-statusline ~/.agent-statusline
chmod +x ~/.agent-statusline/bin/agent-statusline
~/.agent-statusline/bin/agent-statusline codex
```

## Update

```bash
git -C ~/.agent-statusline pull
```

## Requirements

- Python 3.11+ recommended (`tomllib` is used for Codex `config.toml`)
- `git` in `PATH` for repository branch/diff information
- local Codex logs under `~/.codex`
