# Agent Statusline

Generic statusline for AI coding assistants. The project starts with **Codex** support and is intentionally named generically so the same renderer can later support OpenCode and Claude.

Inspired by [`daniel3303/ClaudeCodeStatusLine`](https://github.com/daniel3303/ClaudeCodeStatusLine), but the Codex implementation reads local Codex state instead of Claude Code `statusLine` stdin.

## What Codex shows today

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

Codex currently does not expose the same command-based `statusLine` hook that Claude Code exposes. Until a first-class Codex TUI hook exists, this CLI can be used from shell prompts, tmux, zellij, Warp workflows, or external status bars.

Example zsh prompt segment:

```zsh
alias agent-statusline="$HOME/.agent-statusline/bin/agent-statusline"
agent-statusline codex --no-color
```

## Roadmap

- [x] Codex local log/config provider
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
