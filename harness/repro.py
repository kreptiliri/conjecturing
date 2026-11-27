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
        if len({script.name, *(f.name for f in files)}) != len(files) + 1:
            raise RuntimeError("verifier/shared file basename collision")
        shutil.copy(script, w / script.name)
        for f in files:
            if f.exists():
                shutil.copy(f, w / f.name)
        env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
        p = subprocess.run(["python3", "-I", script.name], cwd=w, env=env,
                           capture_output=True, text=True, timeout=timeout)
        lines = p.stdout.splitlines()
        if p.returncode != 0 or not lines or not lines[-1].startswith("RESULT ") or sum(l.startswith("RESULT ") for l in lines) != 1:
            raise RuntimeError(f"{script.name}: exit {p.returncode}, no RESULT line\n{p.stderr[-2000:]}")
        def unique(pairs):
            obj = {}
            for k, v in pairs:
                if k in obj:
                    raise ValueError(f"duplicate JSON key: {k}")
                obj[k] = v
            return obj
        def invalid_constant(value):
            raise ValueError(f"non-finite JSON value: {value}")
        result = json.loads(lines[-1][len("RESULT "):], object_pairs_hook=unique,
                            parse_constant=invalid_constant)
        if (not isinstance(result, dict) or set(result) != {"witness", "conjecture_holds_at_witness"}
                or type(result["conjecture_holds_at_witness"]) is not bool):
            raise ValueError("RESULT must contain witness and a boolean conjecture_holds_at_witness")
        return result


def compare(a: Path, b: Path, shared: list[Path]) -> tuple[bool, dict, dict]:
    ra, rb = run_verifier(a, shared), run_verifier(b, shared)
    same = json.dumps(ra, sort_keys=True) == json.dumps(rb, sort_keys=True)
    return same, ra, rb
