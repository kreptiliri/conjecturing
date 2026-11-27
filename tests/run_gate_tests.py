"""Gate self-test: the honest solution must pass; every cheat must fail.

Each cheat runs twice: with the lint, and with the lint disabled, to show that
the Lean-level layers (pin, axioms, recheck) catch it on their own as well.
Run: python3 tests/run_gate_tests.py   (needs `lean` on PATH)
"""
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness.gate import run_gate  # noqa: E402

PROBLEM = ROOT / "problems" / "euler-41"
HONEST = ROOT / "examples" / "euler-41" / "Solution.lean"
CHEATS = sorted((ROOT / "tests" / "cheats").glob("*.lean"))


def tampered_problem() -> Path:
    """A copy of the problem whose Challenge.lean was weakened after locking."""
    d = Path(tempfile.mkdtemp()) / "euler-41"
    shutil.copytree(PROBLEM, d)
    p = d / "Challenge.lean"
    p.write_text(p.read_text().replace("∀ n : Nat, IsPrime", "∀ n : Nat, n < 40 → IsPrime"))
    return d


cases = [("honest", PROBLEM, HONEST, "disproof", False, True),
         ("honest, wrong direction", PROBLEM, HONEST, "proof", False, False),
         ("honest, Challenge.lean edited after lock", tampered_problem(), HONEST, "disproof", False, False)]
for c in CHEATS:
    cases.append((f"{c.stem} (lint on)", PROBLEM, c, "disproof", False, False))
    cases.append((f"{c.stem} (lint OFF)", PROBLEM, c, "disproof", True, False))


def go(case):
    name, prob, sol, direction, skip_lint, want = case
    r = run_gate(prob, sol, direction, skip_lint=skip_lint, timeout=600)
    return name, want, r


with ThreadPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(go, cases))

bad = 0
for name, want, r in results:
    good = r.ok == want
    bad += not good
    verdict = "PASS" if r.ok else f"rejected at {r.failed_layer}: {r.reason}"
    print(f"{'ok ' if good else 'BAD'}  {name:<42} {verdict}")
print(f"\n{len(results) - bad}/{len(results)} behaved as expected")
sys.exit(1 if bad else 0)
