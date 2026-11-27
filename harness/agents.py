"""Thin adapter around whatever coding agent CLI you use (Claude Code, Codex, ...).

Agents are untrusted workers. They get a scratch workspace with only the files
their role needs, a role prompt, and a time limit. Nothing they write is
believed until the gate or the reproduction check says so.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    return tomllib.loads((ROOT / "config" / "agents.toml").read_text())


def make_workspace(dest: Path, files: dict[str, Path], readonly: tuple[str, ...] = ("Challenge.lean",)) -> Path:
    if dest.is_symlink():
        raise ValueError("workspace must not be a symlink")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name, src in files.items():
        if src.exists():
            shutil.copy(src, dest / name)
    for name in readonly:
        p = dest / name
        if p.exists():
            p.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return dest


def render_prompt(role: str, extra: str = "") -> str:
    base = (ROOT / "prompts" / f"{role}.md").read_text()
    return base + ("\n\n" + extra if extra else "")


def run_agent(agent: str, role: str, workspace: Path, extra: str = "", timeout: int | None = None) -> int:
    protected = workspace / "Challenge.lean"
    original = protected.read_bytes() if protected.exists() else None
    cfg = load_config()
    a = cfg["agents"][agent]
    prompt = render_prompt(role, extra)
    (workspace / "PROMPT.md").write_text(prompt)
    cmd = [part.replace("{prompt}", prompt).replace("{prompt_file}", str(workspace / "PROMPT.md"))
           .replace("{workdir}", str(workspace)).replace("{root}", str(ROOT)) for part in a["cmd"]]
    env = dict(os.environ)
    for k in cfg.get("strip_env", []):
        env.pop(k, None)
    t = timeout or cfg.get("timeouts", {}).get(role, 3600)
    with open(workspace / f"agent-{role}.log", "w") as log:
        try:
            p = subprocess.run(cmd, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=t)
            code = p.returncode
        except subprocess.TimeoutExpired:
            log.write(f"\n[harness] timed out after {t}s\n")
            code = 124

    # Mode bits are advisory for a same-user agent. Detect replacement and chmod edits.
    if original is not None and (protected.is_symlink() or not protected.exists()
                                 or protected.read_bytes() != original
                                 or protected.stat().st_mode & 0o222):
        if protected.is_symlink() or protected.is_file():
            protected.unlink()
        elif protected.exists():
            shutil.rmtree(protected)
        protected.write_bytes(original)
        protected.chmod(0o444)
        return 125
    return code
