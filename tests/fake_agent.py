"""Scripted stand-in for an agent, so the pipeline can be tested without model calls.
Plays each role for the euler-41 toy using the files in examples/euler-41."""
import json, shutil, sys
from pathlib import Path
EX = Path(__file__).resolve().parent.parent / "examples" / "euler-41"
role = Path(sys.argv[1]).read_text().split("\n", 1)[0].split(":", 1)[1].strip()
here = Path.cwd()
if role == "hunter":
    (here / "candidate.json").write_text(json.dumps({"found": True, "direction": "disproof",
        "witness": {"n": 40}, "claim": "40^2+40+41 = 1681 = 41^2", "scope": "complete"}))
    shutil.copy(EX / "verify.py", here / "verify.py")
    (here / "NOTES.md").write_text("Searched n = 0..1000; first failure at n = 40.\n")
elif role.startswith("independent"):
    shutil.copy(EX / "verify_independent.py", here / "verify_independent.py")
elif role.startswith("Lean"):
    shutil.copy(EX / "Solution.lean", here / "Solution.lean")
elif role.startswith("eligibility"):
    (here / "ELIGIBILITY.md").write_text("# Eligibility\n\nToy problem, known since 1772.\n\nVERDICT: open\n")
elif role.startswith("adversarial"):
    (here / "REVIEW.md").write_text("# Review\n\nToy. Statement matches.\n\nVERDICT: accept\n")
elif role.startswith("prior"):
    (here / "PRIOR_ART.md").write_text("# Prior art\n\nKnown since Euler (1772). Toy problem.\n\nVERDICT: already known\n")
elif role == "writer":
    pass  # leaves the template as is
