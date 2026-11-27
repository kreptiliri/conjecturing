"""The Lean gate: deterministic checks that decide whether a Solution.lean counts.

No agent is involved here. The gate trusts only:
  * the locked Challenge.lean in problems/<slug>/ (checked against challenge.lock),
  * the Lean toolchain,
  * the Check.lean file that this module writes itself.

Layers (each one alone would catch most cheats; together they are the point):
  1. lock     - Challenge.lean hash matches challenge.lock
  2. lint     - solution text: allowed imports only, no banned tokens
  3. compile  - Challenge and Solution compile to .olean in a scratch dir
  4. pin      - Check.lean states the target itself and must accept Solution.main
  5. axioms   - only propext, Classical.choice, Quot.sound (catches sorry,
                native_decide, custom axioms, transitively)
  6. recheck  - leanchecker --fresh re-checks every declaration from the .oleans
  7. paranoid - (optional) leanexport | con-leche, an independent kernel
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

STANDARD_AXIOMS = ("propext", "Classical.choice", "Quot.sound")

# Matched against the solution with comments removed. Word-boundary regexes.
BANNED = {
    r"\bsorry\b": "sorry",
    r"\badmit\b": "admit",
    r"\baxiom\b": "custom axiom",
    r"\bnative_decide\b": "native_decide (trusts the compiler)",
    r"\+native\b": "decide +native",
    r"\bofReduceBool\b": "ofReduceBool",
    r"\btrustCompiler\b": "trustCompiler",
    r"\bimplemented_by\b": "implemented_by",
    r"\bextern\b": "extern",
    r"\bunsafe\b": "unsafe",
    r"\bopaque\b": "opaque",
    r"\bpartial\b": "partial def",
    r"\bdebug\.": "debug.* options",
    r"\brun_cmd\b|\brun_elab\b|\brun_meta\b|\brun_tac\b": "run_* metaprogram",
    r"\belab\b|\belab_rules\b|\bmacro\b|\bmacro_rules\b|\bsyntax\b|\bnotation\b|\binfix[lr]?\b|\bprefix\b|\bpostfix\b": "syntax/macro definitions",
    r"\binitialize\b|\bbuiltin_initialize\b": "initialize",
    r"#eval\b|#exit\b|#print\b": "# commands",
    r"\bLean\.(Elab|Meta|Environment|Kernel|addDecl)\b|\bmodifyEnv\b|\bsetEnv\b": "meta/environment API",
    r"\bnamespace\s+(Challenge|Gate)\b|\b(def|theorem|lemma|abbrev|instance|structure|inductive|class)\s+(Challenge|Gate)\.":
        "declaring inside Challenge/Gate namespace",
    r"\battribute\s*\[\s*(local\s+)?(instance|simp|irreducible|semireducible|reducible)\b[^\]]*\]\s*Challenge\.": "re-attributing Challenge declarations",
    r"\bset_option\s+(?!maxHeartbeats\b|maxRecDepth\b|linter\.)": "set_option (only maxHeartbeats/maxRecDepth/linter.* allowed)",
    r'"': "string literal (banned outright, as on Left to Solve)",
}


@dataclass
class GateResult:
    ok: bool = False
    slug: str = ""
    direction: str = ""
    failed_layer: str = ""
    reason: str = ""
    axioms: list[str] = field(default_factory=list)
    layers_passed: list[str] = field(default_factory=list)
    challenge_sha256: str = ""
    solution_sha256: str = ""
    lean_version: str = ""
    seconds: float = 0.0
    log_tail: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class GateFail(Exception):
    def __init__(self, layer: str, reason: str, log: str = ""):
        super().__init__(reason)
        self.layer, self.reason, self.log = layer, reason, log


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip_comments(src: str) -> str:
    """Remove Lean comments (nested /- -/ blocks and -- lines)."""
    out, i, depth, n = [], 0, 0, len(src)
    while i < n:
        if src.startswith("/-", i):
            depth += 1
            i += 2
        elif depth and src.startswith("-/", i):
            depth -= 1
            i += 2
        elif depth:
            i += 1
        elif src.startswith("--", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        else:
            out.append(src[i])
            i += 1
    if depth:
        raise GateFail("lint", "unterminated block comment")
    return "".join(out)


def lint(solution: str, allow_mathlib: bool) -> None:
    code = strip_comments(solution)
    lines = [l.strip() for l in code.splitlines() if l.strip()]
    imports = [l for l in lines if l.startswith("import ")]
    body = [l for l in lines if not l.startswith("import ")]
    if not imports or imports[0] != "import Challenge":
        raise GateFail("lint", "first import must be `import Challenge`")
    for imp in imports[1:]:
        mod = imp.split(None, 1)[1]
        if not (allow_mathlib and (mod == "Mathlib" or mod.startswith("Mathlib."))):
            raise GateFail("lint", f"import not allowed: {mod}")
    if lines[: len(imports)] != imports:
        raise GateFail("lint", "imports must come first")
    text = "\n".join(body)
    for pat, why in BANNED.items():
        m = re.search(pat, text)
        if m:
            raise GateFail("lint", f"banned: {why} (matched {m.group(0)!r})")
    if not re.search(r"\btheorem\s+(Solution\.)?main\b", text):
        raise GateFail("lint", "no `theorem main` (inside `namespace Solution`) found")


def _clean_env(lean_path: str) -> dict:
    """Minimal environment: no tokens, no credentials leak into Lean/agent code."""
    keep = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "TMPDIR") if k in os.environ}
    keep["LEAN_PATH"] = lean_path
    return keep


def _run(cmd, cwd, env, timeout, layer):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        raise GateFail(layer, f"timeout after {timeout}s: {' '.join(map(str, cmd[:3]))}")
    log = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        raise GateFail(layer, f"exit {p.returncode}: {' '.join(map(str, cmd[:3]))}", log)
    return log


def _toolchain(lake_project: Path | None):
    """Return (lean_binary_dir, base LEAN_PATH)."""
    if lake_project:
        lp = subprocess.run(["lake", "env", "printenv", "LEAN_PATH"], cwd=lake_project,
                            capture_output=True, text=True, check=True).stdout.strip()
        lean = subprocess.run(["lake", "env", "which", "lean"], cwd=lake_project,
                              capture_output=True, text=True, check=True).stdout.strip()
        return Path(lean).parent, lp
    lean = shutil.which("lean")
    if not lean:
        raise GateFail("compile", "lean not found on PATH (install elan, or pass --lake-project)")
    return Path(lean).resolve().parent, str(Path(lean).resolve().parent.parent / "lib" / "lean")


CHECK_TEMPLATE = """import Challenge
import Solution

/-- The gate writes the target itself. The solution cannot choose it. -/
theorem Gate.pinned : {target} := Solution.main
"""

# Separate file so that `leanchecker --fresh Check` does not have to recheck all of `Lean`.
AUDIT_TEMPLATE = """import Check
import Lean

open Lean Elab Command in
run_cmd do
  let allowed : Array Name := #[{allowed}]
  let axs ← Lean.collectAxioms ``Gate.pinned
  logInfo m!"GATE_AXIOMS {{axs.toList}}"
  for a in axs do
    unless allowed.contains a do
      throwError m!"GATE_FAIL non-standard axiom {{a}}"
"""


def run_gate(problem_dir: Path, solution_file: Path, direction: str, *,
             lake_project: Path | None = None,
             timeout: int = 1800, mem_gb: int = 8, paranoid: bool = False,
             skip_lint: bool = False) -> GateResult:
    t0 = time.time()
    res = GateResult(slug=problem_dir.name, direction=direction)
    challenge = problem_dir / "Challenge.lean"
    lock = problem_dir / "challenge.lock"
    try:
        if direction not in ("proof", "disproof"):
            raise GateFail("pin", "direction must be 'proof' or 'disproof'")
        # 1. lock
        if not lock.exists():
            raise GateFail("lock", "challenge.lock missing: run `harness lock <slug>` after a human reviews Challenge.lean")
        want = json.loads(lock.read_text())["sha256"]
        res.challenge_sha256 = sha256(challenge)
        if res.challenge_sha256 != want:
            raise GateFail("lock", "Challenge.lean changed since it was locked")
        res.layers_passed.append("lock")
        res.solution_sha256 = sha256(solution_file)
        # 2. lint
        if not skip_lint:
            lint(solution_file.read_text(), allow_mathlib=lake_project is not None)
            res.layers_passed.append("lint")
        # 3. compile
        bindir, base_path = _toolchain(lake_project)
        lean = str(bindir / "lean")
        mem = f"-M{mem_gb * 1024}"   # Lean's own memory cap (MB); RLIMIT_AS breaks .olean mmap
        with tempfile.TemporaryDirectory(prefix="gate-") as td:
            w = Path(td)
            (w / "out").mkdir()
            shutil.copy(challenge, w / "Challenge.lean")          # the LOCKED copy
            shutil.copy(solution_file, w / "Solution.lean")
            target = "Challenge.Conjecture" if direction == "proof" else "¬ Challenge.Conjecture"
            allowed = ", ".join(f"``{a}" for a in STANDARD_AXIOMS)
            (w / "Check.lean").write_text(CHECK_TEMPLATE.format(target=target))
            (w / "Audit.lean").write_text(AUDIT_TEMPLATE.format(allowed=allowed))
            env = _clean_env(f"{w / 'out'}{os.pathsep}{base_path}")
            res.lean_version = subprocess.run([lean, "--version"], capture_output=True, text=True).stdout.strip()
            run = lambda cmd, layer: _run(cmd, w, env, timeout, layer)
            run([lean, mem, "-o", "out/Challenge.olean", "Challenge.lean"], "compile")
            run([lean, mem, "-o", "out/Solution.olean", "Solution.lean"], "compile")
            res.layers_passed.append("compile")
            # 4. pin: the locked target must be proved by Solution.main
            try:
                run([lean, mem, "-o", "out/Check.olean", "Check.lean"], "pin")
            except GateFail as e:
                e.reason = "Solution.main does not prove the pinned target (or is missing)"
                raise
            res.layers_passed.append("pin")
            # 5. axioms, collected transitively
            try:
                log = run([lean, mem, "Audit.lean"], "axioms")
            except GateFail as e:
                if "GATE_FAIL non-standard axiom" in e.log:
                    e.reason = "non-standard axiom: " + e.log.split("GATE_FAIL non-standard axiom", 1)[1].split()[0]
                raise
            m = re.search(r"GATE_AXIOMS \[(.*?)\]", log)
            res.axioms = [a.strip() for a in m.group(1).split(",") if a.strip()] if m else []
            res.layers_passed.append("axioms")
            # 6. recheck every declaration from the .oleans
            checker = bindir / "leanchecker"
            if checker.exists():
                run([str(checker), "--fresh", "Check"], "recheck")
                res.layers_passed.append("recheck")
            else:
                res.log_tail += "warning: leanchecker not found; recheck skipped\n"
            # 7. optional independent kernel
            if paranoid:
                exp, cl = bindir / "leanexport", bindir / "con-leche"
                if not (exp.exists() and cl.exists()):
                    raise GateFail("paranoid", "leanexport/con-leche not in toolchain (need Lean >= 4.35)")
                with open(w / "check.ndjson", "w") as fh:
                    subprocess.run([str(exp), "Check"], cwd=w, env=env, stdout=fh, check=True, timeout=timeout)
                log = run([str(cl), "check.ndjson"], "paranoid")
                if "accepted" not in log:
                    raise GateFail("paranoid", "con-leche did not accept", log)
                res.layers_passed.append("paranoid")
        res.ok = True
    except GateFail as e:
        res.failed_layer, res.reason = e.layer, e.reason
        res.log_tail += "\n".join((e.log or "").splitlines()[-40:])
    res.seconds = round(time.time() - t0, 2)
    return res
