"""Reproduction check: two independently written Python verifiers must agree.

Each script must print a final line `RESULT {json}`. The JSON objects are
compared exactly (after canonical sorting). Python is evidence, not proof:
it decides whether a candidate is worth formalizing, never whether it counts.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def run_verifier(script: Path, files: list[Path], timeout: int = 600) -> dict:
    with tempfile.TemporaryDirectory(prefix="repro-") as td:
        w = Path(td)
        shutil.copy(script, w / script.name)
        for f in files:
            if f.exists():
                shutil.copy(f, w / f.name)
        env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
        p = subprocess.run(["python3", "-I", script.name], cwd=w, env=env,
                           capture_output=True, text=True, timeout=timeout)
        lines = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
        if p.returncode != 0 or not lines:
            raise RuntimeError(f"{script.name}: exit {p.returncode}, no RESULT line\n{p.stderr[-2000:]}")
        return json.loads(lines[-1][len("RESULT "):])


def compare(a: Path, b: Path, shared: list[Path]) -> tuple[bool, dict, dict]:
    ra, rb = run_verifier(a, shared), run_verifier(b, shared)
    same = json.dumps(ra, sort_keys=True) == json.dumps(rb, sort_keys=True)
    return same, ra, rb
