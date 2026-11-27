"""The pipeline: hunt -> reproduce -> formalize (gate loop) -> prior art -> writeup -> package.

Trust boundaries:
  * Hunters see problem.md + Challenge.lean. They produce candidate.json + verify.py.
  * The reproducer sees problem.md + candidate.json ONLY (never the hunter's code).
  * The formalizer sees the locked statement, candidate, and gate feedback.
  * The gate is code, not an agent. The final semantic check is you.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import agents, gate, repro

ROOT = Path(__file__).resolve().parent.parent


def problem_dir(slug: str) -> Path:
    d = ROOT / "problems" / slug
    if not (d / "Challenge.lean").exists():
        raise SystemExit(f"no problems/{slug}/Challenge.lean")
    return d


def research_dir(slug: str) -> Path:
    """Committed notes: eligibility checks and failed attempts, so nobody redoes them."""
    d = ROOT / "research" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def front_matter(md: Path) -> dict:
    lines = md.read_text().splitlines()
    out = {}
    if lines and lines[0].strip() == "---":
        for l in lines[1:]:
            if l.strip() == "---":
                break
            if ":" in l:
                k, v = l.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def verdict(path: Path) -> str:
    """Last `VERDICT: x` line of an agent report, lowercased; 'missing' if none."""
    if not path.exists():
        return "missing"
    for line in reversed(path.read_text().splitlines()):
        line = line.strip().strip("`*").strip()
        if line.upper().startswith("VERDICT:"):
            return line.split(":", 1)[1].strip().strip("`*").lower()
    return "missing"


def run_dir(slug: str) -> Path:
    d = ROOT / "runs" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def state(slug: str) -> dict:
    p = run_dir(slug) / "state.json"
    return json.loads(p.read_text()) if p.exists() else {"slug": slug, "stages": {}}


def save_state(slug: str, st: dict) -> None:
    (run_dir(slug) / "state.json").write_text(json.dumps(st, indent=2))


def mark(slug: str, stage: str, **info) -> None:
    st = state(slug)
    st["stages"][stage] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **info}
    save_state(slug, st)


# ---------------------------------------------------------------- before hunting
def duplicates(slug: str) -> list[str]:
    """Other problems/results with the same source and statement number."""
    me = front_matter(problem_dir(slug) / "problem.md")
    key = (me.get("source_id", "").lower(), me.get("statement", "").lower())
    if not all(key):
        return []
    hits = []
    for md in list((ROOT / "problems").glob("*/problem.md")) + list((ROOT / "results").glob("*/problem.md")):
        if md.parent.name == slug:
            continue
        fm = front_matter(md)
        if (fm.get("source_id", "").lower(), fm.get("statement", "").lower()) == key:
            hits.append(str(md.parent.relative_to(ROOT)))
    return sorted(set(hits))


def eligibility(slug: str, agent: str) -> str:
    pd = problem_dir(slug)
    ws = agents.make_workspace(run_dir(slug) / "eligibility", {
        "problem.md": pd / "problem.md", "Challenge.lean": pd / "Challenge.lean"})
    agents.run_agent(agent, "eligibility", ws)
    v = verdict(ws / "ELIGIBILITY.md")
    if (ws / "ELIGIBILITY.md").exists():
        shutil.copy(ws / "ELIGIBILITY.md", research_dir(slug) / "ELIGIBILITY.md")
    mark(slug, "eligibility", verdict=v)
    return v


def archive_attempts(slug: str, dirs: list[Path]) -> Path:
    """Keep every hunter's notes (including failures) in research/<slug>/."""
    out = research_dir(slug) / f"ATTEMPTS-{time.strftime('%Y%m%d-%H%M%S')}.md"
    parts = [f"# Hunt attempts for {slug}\n"]
    for d in dirs:
        cand = (d / "candidate.json").read_text() if (d / "candidate.json").exists() else "(no candidate.json)"
        notes = (d / "NOTES.md").read_text() if (d / "NOTES.md").exists() else "(no NOTES.md)"
        parts.append(f"## {d.name}\n\n```json\n{cand.strip()}\n```\n\n{notes.strip()}\n")
    out.write_text("\n".join(parts))
    return out


# ---------------------------------------------------------------- hunt
def hunt(slug: str, agent: str, n: int) -> list[Path]:
    pd = problem_dir(slug)
    base = run_dir(slug)
    def one(i: int) -> Path:
        ws = agents.make_workspace(base / f"hunt-{i:02d}", {
            "problem.md": pd / "problem.md", "Challenge.lean": pd / "Challenge.lean"})
        agents.run_agent(agent, "hunter", ws, extra=f"You are hunter #{i} of {n}. "
                         f"Pick a search strategy different from the obvious one if i > 1 (i={i}).")
        return ws
    with ThreadPoolExecutor(max_workers=n) as ex:
        dirs = list(ex.map(one, range(1, n + 1)))
    archive_attempts(slug, dirs)
    found = []
    for d in dirs:
        c = d / "candidate.json"
        if c.exists() and (d / "verify.py").exists():
            try:
                if json.loads(c.read_text()).get("found"):
                    found.append(d)
            except json.JSONDecodeError:
                pass
    mark(slug, "hunt", hunters=n, candidates=[d.name for d in found])
    return found


# ---------------------------------------------------------------- reproduce
def reproduce(slug: str, agent: str, cand_dir: Path) -> bool:
    pd = problem_dir(slug)
    ws = agents.make_workspace(cand_dir.parent / f"repro-{cand_dir.name}", {
        "problem.md": pd / "problem.md", "candidate.json": cand_dir / "candidate.json"})
    agents.run_agent(agent, "reproducer", ws)
    ind = ws / "verify_independent.py"
    if not ind.exists():
        mark(slug, "reproduce", ok=False, reason="reproducer wrote no verify_independent.py")
        return False
    same, ra, rb = repro.compare(cand_dir / "verify.py", ind, [cand_dir / "candidate.json"])
    shutil.copy(ind, cand_dir / "verify_independent.py")
    mark(slug, "reproduce", ok=same, hunter=ra, independent=rb, candidate=cand_dir.name)
    return same


# ---------------------------------------------------------------- formalize
def formalize(slug: str, agent: str, cand_dir: Path, direction: str, iters: int = 6, **gate_kw) -> gate.GateResult:
    pd = problem_dir(slug)
    ws = agents.make_workspace(cand_dir.parent / f"lean-{cand_dir.name}", {
        "problem.md": pd / "problem.md", "Challenge.lean": pd / "Challenge.lean",
        "candidate.json": cand_dir / "candidate.json", "NOTES.md": cand_dir / "NOTES.md"})
    res = gate.GateResult(reason="formalizer produced no Solution.lean")
    for k in range(1, iters + 1):
        agents.run_agent(agent, "formalizer", ws, extra=f"Target direction: {direction}. Attempt {k} of {iters}.")
        sol = ws / "Solution.lean"
        if not sol.exists():
            continue
        res = gate.run_gate(pd, sol, direction, **gate_kw)
        (ws / "GATE_RECEIPT.json").write_text(res.to_json())
        if res.ok:
            shutil.copy(sol, cand_dir / "Solution.lean")
            shutil.copy(ws / "GATE_RECEIPT.json", cand_dir / "GATE_RECEIPT.json")
            break
        (ws / "FEEDBACK.md").write_text(
            f"# Gate rejected attempt {k}\n\nLayer: {res.failed_layer}\nReason: {res.reason}\n\n```\n{res.log_tail}\n```\n")
    mark(slug, "formalize", ok=res.ok, attempts=k, failed_layer=res.failed_layer, reason=res.reason)
    return res


# ---------------------------------------------------------------- prior art + writeup
def prior_art(slug: str, agent: str, cand_dir: Path) -> None:
    pd = problem_dir(slug)
    ws = agents.make_workspace(cand_dir.parent / f"prior-{cand_dir.name}", {
        "problem.md": pd / "problem.md", "candidate.json": cand_dir / "candidate.json"})
    agents.run_agent(agent, "prior_art", ws)
    if (ws / "PRIOR_ART.md").exists():
        shutil.copy(ws / "PRIOR_ART.md", cand_dir / "PRIOR_ART.md")
    mark(slug, "prior_art", written=(cand_dir / "PRIOR_ART.md").exists())


def writeup(slug: str, agent: str, cand_dir: Path) -> Path | None:
    pd = problem_dir(slug)
    files = {n: cand_dir / n for n in ("candidate.json", "NOTES.md", "Solution.lean", "GATE_RECEIPT.json",
                                       "verify.py", "verify_independent.py", "PRIOR_ART.md")}
    files |= {"problem.md": pd / "problem.md", "Challenge.lean": pd / "Challenge.lean",
              "paper.tex": ROOT / "templates" / "paper.tex"}
    ws = agents.make_workspace(cand_dir.parent / f"paper-{cand_dir.name}", files)
    agents.run_agent(agent, "writer", ws)
    pdf = build_pdf(ws / "paper.tex")
    for f in ("paper.tex", "paper.pdf"):
        if (ws / f).exists():
            shutil.copy(ws / f, cand_dir / f)
    mark(slug, "writeup", pdf=bool(pdf))
    return pdf


def build_pdf(tex: Path) -> Path | None:
    for cmd in (["latexmk", "-pdf", "-interaction=nonstopmode", tex.name],
                ["tectonic", tex.name],
                ["pdflatex", "-interaction=nonstopmode", tex.name]):
        if shutil.which(cmd[0]):
            subprocess.run(cmd, cwd=tex.parent, capture_output=True, timeout=600)
            pdf = tex.with_suffix(".pdf")
            if pdf.exists():
                return pdf
    return None


def referee(slug: str, agent: str, cand_dir: Path) -> str:
    pd = problem_dir(slug)
    files = {n: cand_dir / n for n in ("paper.tex", "paper.pdf", "candidate.json", "PRIOR_ART.md", "NOTES.md")}
    files |= {"problem.md": pd / "problem.md", "Challenge.lean": pd / "Challenge.lean"}
    ws = agents.make_workspace(cand_dir.parent / f"referee-{cand_dir.name}", files)
    agents.run_agent(agent, "referee", ws)
    if (ws / "REVIEW.md").exists():
        shutil.copy(ws / "REVIEW.md", cand_dir / "REVIEW.md")
    v = verdict(cand_dir / "REVIEW.md")
    mark(slug, "referee", verdict=v)
    return v


# ---------------------------------------------------------------- package
RESULT_FILES = ("Solution.lean", "verify.py", "verify_independent.py", "candidate.json",
                "GATE_RECEIPT.json", "PRIOR_ART.md", "REVIEW.md", "paper.tex", "paper.pdf", "NOTES.md")


def package(slug: str, cand_dir: Path) -> Path:
    pd = problem_dir(slug)
    out = ROOT / "results" / slug
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(pd / "Challenge.lean", out / "Challenge.lean")
    shutil.copy(pd / "challenge.lock", out / "challenge.lock")
    shutil.copy(pd / "problem.md", out / "problem.md")
    elig = ROOT / "research" / slug / "ELIGIBILITY.md"
    if elig.exists():
        shutil.copy(elig, out / "ELIGIBILITY.md")
    for f in RESULT_FILES:
        if (cand_dir / f).exists():
            shutil.copy(cand_dir / f, out / f)
    write_readme(slug)
    mark(slug, "package", path=str(out.relative_to(ROOT)))
    return out


def write_readme(slug: str) -> None:
    out = ROOT / "results" / slug
    receipt = json.loads((out / "GATE_RECEIPT.json").read_text()) if (out / "GATE_RECEIPT.json").exists() else {}
    cand = json.loads((out / "candidate.json").read_text()) if (out / "candidate.json").exists() else {}
    tmpl = (ROOT / "templates" / "result_README.md").read_text()
    (out / "README.md").write_text(tmpl.format(
        slug=slug,
        direction=receipt.get("direction", "?"),
        gate="passed" if receipt.get("ok") else "NOT passed",
        layers=", ".join(receipt.get("layers_passed", [])),
        axioms=", ".join(receipt.get("axioms", [])) or "none",
        lean=receipt.get("lean_version", "?"),
        challenge_sha=receipt.get("challenge_sha256", "?"),
        solution_sha=receipt.get("solution_sha256", "?"),
        pdf="[paper.pdf](paper.pdf)" if (out / "paper.pdf").exists() else "not built",
        scope=cand.get("scope", "?"),
        eligibility=verdict(out / "ELIGIBILITY.md"),
        prior=verdict(out / "PRIOR_ART.md"),
        referee=verdict(out / "REVIEW.md"),
        approved="yes, see APPROVAL.md" if (out / "APPROVAL.md").exists() else "**no: awaiting human review**",
    ))
