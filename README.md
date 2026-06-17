# Agent Statusline

Generic statusline for AI coding assistants. The project starts with **Codex** support and is intentionally named generically so the same renderer can later support OpenCode and Claude.

Inspired by [`daniel3303/ClaudeCodeStatusLine`](https://github.com/daniel3303/ClaudeCodeStatusLine), but the Codex implementation reads local Codex state instead of Claude Code `statusLine` stdin.

## Codex Native Status Line

Codex has a native status line configured in `~/.codex/config.toml` under `[tui]`:

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "project-name", "git-branch"]
status_line_use_colors = true
```

Install the recommended native Codex status line:

```bash
~/.agent-statusline/bin/install-codex-statusline
```

The native Codex picker currently exposes built-in items such as model, reasoning, current directory, project name, and git branch. The richer CLI below exists for extra local telemetry that is not available as a native item yet.

## Native `/statusline` vs `agent-statusline`

The status line shown inside the Codex TUI is Codex's native `/statusline`, not this project's CLI output. This project currently complements the native bar; it does not replace it automatically.

| Feature | Codex `/statusline` | `agent-statusline` |
| --- | --- | --- |
| Runs inside the Codex TUI | Yes | Not yet |
| Configuration | `/statusline` UI or `[tui].status_line` | CLI arguments and future adapters |
| Available fields | Built-in Codex items only | Can read Codex config, logs, SQLite, git, and future providers |
| Best for | Stable native model/dir/limits display | Experiments, richer telemetry, tmux/zellij/Warp, OpenCode/Claude support |

## Why This Is Not Like Claude Yet

Claude Code supports a command-backed status line: Claude runs a script, passes session JSON on stdin, and renders the script output inside the TUI. That is what projects like `ClaudeCodeStatusLine` use.

Codex does not currently expose that same custom command hook. Codex's native `/statusline` is a picker for built-in items. The long-term goal for this project is to become the command/provider used by Codex if Codex adds command-backed statusline support. Until then, `agent-statusline` is a companion CLI and integration target for shells, tmux, zellij, Warp, and future providers.

## Extra Codex Telemetry CLI

- current/last Codex model
- current workspace folder, git branch, and added/deleted diff stats
- latest Codex token usage from `~/.codex/sqlite/logs_2.sqlite` or `~/.codex/logs_2.sqlite`
- reasoning effort
- service tier
- approval/sandbox policy
- auth mode and Codex app version when present in local logs

Example:

```text
gpt-5.5 | agent-statusline@main (+12 -0) | 48k/245k (19%) | effort: med | tier: fast | policy: never/danger-full-access | auth: Chatgpt | 7s ago | v0.140.0
```

## Install locally

```bash
git clone https://github.com/juanitourquiza/agent-statusline ~/.agent-statusline
chmod +x ~/.agent-statusline/bin/agent-statusline
~/.agent-statusline/bin/agent-statusline codex
```

Or from this checkout:

```bash
./bin/agent-statusline codex
```

## Usage

```bash
agent-statusline codex
agent-statusline codex --no-color
agent-statusline codex --json
```

Optional environment variables:

- `CODEX_HOME`: override the Codex config/log directory. Defaults to `~/.codex`.

## Shell integration ideas

Codex has native built-in status line items. For fields beyond those built-ins, this CLI can be used from shell prompts, tmux, zellij, Warp workflows, or external status bars.

Example zsh prompt segment:

```zsh
alias agent-statusline="$HOME/.agent-statusline/bin/agent-statusline"
agent-statusline codex --no-color
```

## Roadmap

- [x] Codex local log/config provider
- [ ] Track Codex command-backed/custom statusline support
- [ ] Codex rate-limit/source-of-truth research
- [ ] tmux/zellij snippets
- [ ] OpenCode provider
- [ ] Claude provider adapter
- [ ] Windows PowerShell wrapper

## Attribution

This project is inspired by the compact segment design of `daniel3303/ClaudeCodeStatusLine`.
Implementation here is separate and focused first on Codex local telemetry.

## License

MIT
