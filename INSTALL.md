# Installation

## macOS / Linux

```bash
git clone https://github.com/juanitourquiza/agent-statusline ~/.agent-statusline
chmod +x ~/.agent-statusline/bin/agent-statusline
~/.agent-statusline/bin/agent-statusline codex
```

Then configure the native Codex status line:

```bash
~/.agent-statusline/bin/install-codex-statusline
```

This updates `~/.codex/config.toml`:

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "project-name", "git-branch"]
status_line_use_colors = true
```

Restart Codex or open a new TUI session after changing the config.

## Update

```bash
git -C ~/.agent-statusline pull
```

## Requirements

- Python 3.11+ recommended (`tomllib` is used for Codex `config.toml`)
- `git` in `PATH` for repository branch/diff information
- local Codex logs under `~/.codex`
