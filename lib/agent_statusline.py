#!/usr/bin/env python3
"""Generic AI coding assistant statusline.

Initial provider: Codex. Reads local Codex config and telemetry logs without
requiring network calls or secrets. Designed so OpenCode/Claude providers can be
added behind the same renderer later.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

VERSION = "0.1.0"
DEFAULT_CODEX_CONTEXT_WINDOW = 1_000_000

COLORS = {
    "blue": "\033[38;2;0;153;255m",
    "orange": "\033[38;2;255;176;85m",
    "green": "\033[38;2;0;160;0m",
    "cyan": "\033[38;2;46;149;153m",
    "red": "\033[38;2;255;85;85m",
    "yellow": "\033[38;2;230;200;0m",
    "purple": "\033[38;2;167;139;250m",
    "white": "\033[38;2;220;220;220m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}


def color(name: str, text: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{COLORS[name]}{text}{COLORS['reset']}"


def sep(enabled: bool) -> str:
    return f" {color('dim', '|', enabled)} "


def format_tokens(value: int) -> str:
    if value >= 1_000_000:
        n = value / 1_000_000
        return f"{n:.1f}m" if n % 1 else f"{int(n)}m"
    if value >= 1_000:
        return f"{round(value / 1_000):.0f}k"
    return str(value)


def usage_color(pct: int) -> str:
    if pct >= 90:
        return "red"
    if pct >= 70:
        return "orange"
    if pct >= 50:
        return "yellow"
    return "green"


def run(cmd: list[str], cwd: str | None = None) -> str:
    try:
        return subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def read_toml(path: Path) -> dict[str, Any]:
    if not path.exists() or tomllib is None:
        return {}
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return {}


@dataclass
class GitInfo:
    cwd: str
    branch: str = ""
    added: int = 0
    deleted: int = 0


def git_info(cwd: str) -> GitInfo:
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    added = deleted = 0
    diff = run(["git", "diff", "--numstat"], cwd=cwd)
    for line in diff.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            added += int(parts[0])
            deleted += int(parts[1])
    return GitInfo(cwd=cwd, branch=branch, added=added, deleted=deleted)


@dataclass
class CodexSnapshot:
    model: str
    effort: str
    cwd: str
    total_usage_tokens: int = 0
    estimated_token_count: int = 0
    context_limit: int = DEFAULT_CODEX_CONTEXT_WINDOW
    approval_policy: str = ""
    sandbox_mode: str = ""
    service_tier: str = ""
    auth_mode: str = ""
    app_version: str = ""
    thread_id: str = ""
    age_seconds: int = 0


class CodexProvider:
    def __init__(self, codex_home: Path):
        self.codex_home = codex_home
        self.config = read_toml(codex_home / "config.toml")
        self.db = self._find_logs_db()

    def _find_logs_db(self) -> Path:
        candidates = [
            self.codex_home / "sqlite" / "logs_2.sqlite",
            self.codex_home / "logs_2.sqlite",
        ]
        existing = [path for path in candidates if path.exists()]
        if existing:
            return max(existing, key=lambda p: p.stat().st_mtime)
        return candidates[0]

    def snapshot(self) -> CodexSnapshot:
        model = str(self.config.get("model") or "codex")
        effort = str(self.config.get("model_reasoning_effort") or "")
        cwd = os.getcwd()
        snap = CodexSnapshot(
            model=model,
            effort=effort,
            cwd=cwd,
            approval_policy=str(self.config.get("approval_policy") or ""),
            sandbox_mode=str(self.config.get("sandbox_mode") or ""),
            service_tier=str(self.config.get("service_tier") or ""),
        )
        if self.db.exists():
            self._merge_latest_log_snapshot(snap)
        return snap

    def _merge_latest_log_snapshot(self, snap: CodexSnapshot) -> None:
        try:
            conn = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True, timeout=0.2)
        except Exception:
            return
        try:
            conn.row_factory = sqlite3.Row
            token_row = conn.execute(
                """
                select ts, feedback_log_body from logs
                where feedback_log_body like '%post sampling token usage%'
                order by ts desc, ts_nanos desc, id desc limit 1
                """
            ).fetchone()
            if token_row:
                body = token_row["feedback_log_body"] or ""
                snap.total_usage_tokens = int_match(body, r"total_usage_tokens=(\d+)")
                snap.estimated_token_count = int_match(body, r"estimated_token_count=Some\((\d+)\)")
                limit = int_match(body, r"auto_compact_scope_limit=(\d+)") or int_match(body, r"full_context_window_limit=(\d+)")
                if limit:
                    snap.context_limit = limit
                snap.thread_id = str_match(body, r"thread_id=([0-9a-f\-]+)") or snap.thread_id
                snap.age_seconds = max(0, int(time.time()) - int(token_row["ts"]))

            meta_row = conn.execute(
                """
                select ts, feedback_log_body from logs
                where feedback_log_body like '%run_sampling_request%' or feedback_log_body like '%event.name="codex.websocket_request"%'
                order by ts desc, ts_nanos desc, id desc limit 1
                """
            ).fetchone()
            if meta_row:
                body = meta_row["feedback_log_body"] or ""
                # Prefer the turn/request model over telemetry dimensions such as slug/model in
                # appended event fields. Unquoted model= appears in request spans.
                snap.model = str_match(body, r"run_sampling_request\{[^}]*model=([^\s}]+)") or str_match(body, r"try_run_sampling_request\{[^}]*model=([^\s}]+)") or str_match(body, r"model=\"([^\"]+)\"") or str_match(body, r"model=([^\s}]+)") or snap.model
                snap.effort = str_match(body, r"codex\.turn\.reasoning_effort=([^}:\s]+)") or str_match(body, r"codex\.request\.reasoning_effort=([^\s}]+)") or snap.effort
                snap.cwd = str_match(body, r"cwd=([^}:]+)") or snap.cwd
                snap.auth_mode = str_match(body, r"auth_mode=\"([^\"]+)\"") or snap.auth_mode
                snap.app_version = str_match(body, r"app\.version=([^\s]+)") or snap.app_version
                snap.thread_id = str_match(body, r"thread_id=([0-9a-f\-]+)") or snap.thread_id
        finally:
            conn.close()


def int_match(text: str, pattern: str) -> int:
    m = re.search(pattern, text)
    return int(m.group(1)) if m else 0


def str_match(text: str, pattern: str) -> str:
    m = re.search(pattern, text)
    return m.group(1).strip('"') if m else ""


def render_codex(snapshot: CodexSnapshot, color_enabled: bool) -> str:
    parts: list[str] = [color("blue", snapshot.model, color_enabled)]

    gi = git_info(snapshot.cwd) if snapshot.cwd else GitInfo(cwd=os.getcwd())
    dirname = Path(snapshot.cwd).name or snapshot.cwd
    repo = color("cyan", dirname, color_enabled)
    if gi.branch:
        repo += color("dim", "@", color_enabled) + color("green", gi.branch, color_enabled)
        if gi.added or gi.deleted:
            repo += " " + color("dim", "(", color_enabled)
            repo += color("green", f"+{gi.added}", color_enabled)
            repo += " " + color("red", f"-{gi.deleted}", color_enabled)
            repo += color("dim", ")", color_enabled)
    parts.append(repo)

    current = snapshot.total_usage_tokens or snapshot.estimated_token_count
    pct = int((current * 100) / snapshot.context_limit) if snapshot.context_limit else 0
    token_text = f"{format_tokens(current)}/{format_tokens(snapshot.context_limit)}"
    token_text += f" {color('dim', '(', color_enabled)}{color(usage_color(pct), str(pct) + '%', color_enabled)}{color('dim', ')', color_enabled)}"
    parts.append(color("orange", token_text.split()[0], color_enabled) + " " + " ".join(token_text.split()[1:]))

    if snapshot.effort:
        effort_label = {"medium": "med"}.get(snapshot.effort, snapshot.effort)
        effort_col = {"low": "dim", "medium": "orange", "high": "green", "xhigh": "purple", "max": "red"}.get(snapshot.effort, "green")
        parts.append(f"effort: {color(effort_col, effort_label, color_enabled)}")

    if snapshot.service_tier:
        parts.append(f"tier: {color('green', snapshot.service_tier, color_enabled)}")
    if snapshot.approval_policy or snapshot.sandbox_mode:
        policy = "/".join(x for x in [snapshot.approval_policy, snapshot.sandbox_mode] if x)
        parts.append(f"policy: {color('purple', policy, color_enabled)}")
    if snapshot.auth_mode:
        parts.append(f"auth: {color('white', snapshot.auth_mode, color_enabled)}")
    if snapshot.age_seconds:
        parts.append(color("dim", f"{snapshot.age_seconds}s ago", color_enabled))
    if snapshot.app_version:
        parts.append(color("orange", f"v{snapshot.app_version}", color_enabled))

    return sep(color_enabled).join(parts)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generic AI agent statusline")
    parser.add_argument("provider", nargs="?", default="codex", choices=["codex"], help="provider to render")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--json", action="store_true", help="print provider snapshot as JSON")
    parser.add_argument("--version", action="version", version=f"agent-statusline {VERSION}")
    args = parser.parse_args(argv)

    if args.provider == "codex":
        snap = CodexProvider(Path(args.codex_home).expanduser()).snapshot()
        if args.json:
            print(json.dumps(snap.__dict__, ensure_ascii=False, indent=2))
        else:
            print(render_codex(snap, not args.no_color))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
