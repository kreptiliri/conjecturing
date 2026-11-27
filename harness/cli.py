"""Command line: python -m harness <command> ...

  new <slug>                      scaffold problems/<slug>/
  lock <slug>                     record Challenge.lean hash (after YOU read it)
  gate <slug> <Solution.lean> --direction proof|disproof [--lake-project DIR] [--paranoid]
  repro <a.py> <b.py> [files...]  compare two verifiers' RESULT lines
  run <slug> --agent claude --hunters 4 --direction disproof
  dupes <slug>                    same source + statement already here?
  approve <slug> --name "You"     human sign-off on the statement's meaning
  verify-results                  re-gate everything in results/ (CI)
  status [slug]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import gate, pipeline, repro

ROOT = pipeline.ROOT


PROBLEM_TEMPLATE = """---
slug: {slug}
title:
source: Authors, Title
source_id: arXiv:XXXX.XXXXXvN
statement: Conjecture X.Y
page:
source_url:
area:
expected: unknown
---

# Statement

(Exact wording from the source, copied from the version in source_id.)

# Statement check (fill in before `harness lock`)

Compare Challenge.lean to the source, hypothesis by hypothesis. Tick each box, or
write what differs. The gate checks proofs; only this checks the statement.

- [ ] Every hypothesis in the source appears in Challenge.lean, none added
- [ ] Domains and objects match (simple graph? labeled? which field/ring?)
- [ ] Quantifiers and their order match
- [ ] Edge cases match: smallest admissible size, n = 0/1, empty objects
- [ ] Strict vs non-strict inequalities, indexing conventions match
- [ ] If copied from formal-conjectures: their statement matches the source too

# Notes for agents

- Formal statement: `Challenge.lean`. Do not edit it.
"""


def cmd_new(a):
    d = ROOT / "problems" / a.slug
    d.mkdir(parents=True, exist_ok=False)
    (d / "problem.md").write_text(PROBLEM_TEMPLATE.format(slug=a.slug))
    (d / "Challenge.lean").write_text(
        "/- Locked statement. Copy from google-deepmind/formal-conjectures when it exists there. -/\n"
        "import Mathlib\n\nnamespace Challenge\n\n/-- The conjecture, as a Prop. -/\n"
        "def Conjecture : Prop := sorry\n\nend Challenge\n")
    print(f"created {d}. Fill problem.md (source + statement check) and Challenge.lean, then: "
          f"python -m harness lock {a.slug} --name ...")


def cmd_lock(a):
    d = pipeline.problem_dir(a.slug)
    src = (d / "Challenge.lean").read_text()
    if "sorry" in gate.strip_comments(src):
        sys.exit("Challenge.lean still contains sorry")
    md = (d / "problem.md").read_text()
    fm = pipeline.front_matter(d / "problem.md")
    missing = [k for k in ("source_id", "statement", "source_url") if not fm.get(k) or "XXXX" in fm.get(k, "") or "X.Y" in fm.get(k, "")]
    if missing:
        sys.exit(f"problem.md: fill in {', '.join(missing)} first (exact source pinning)")
    if "- [ ]" in md:
        sys.exit("problem.md: the statement check still has unticked boxes. Compare Challenge.lean "
                 "to the source and tick each one, or explain the difference")
    dupes = pipeline.duplicates(a.slug)
    if dupes:
        sys.exit(f"same source and statement already in: {', '.join(dupes)}")
    (d / "challenge.lock").write_text(json.dumps({
        "sha256": gate.sha256(d / "Challenge.lean"),
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reviewed_by": a.name}, indent=2) + "\n")
    print(f"locked {a.slug}: {gate.sha256(d / 'Challenge.lean')[:16]}…")


def cmd_gate(a):
    r = gate.run_gate(pipeline.problem_dir(a.slug), Path(a.solution), a.direction,
                      lake_project=Path(a.lake_project) if a.lake_project else None,
                      paranoid=a.paranoid, strict=a.strict, timeout=a.timeout, mem_gb=a.mem_gb)
    if a.receipt:
        Path(a.receipt).write_text(r.to_json())
    status = "PASS" if r.ok else f"FAIL [{r.failed_layer}] {r.reason}"
    print(f"{status}\n  layers: {', '.join(r.layers_passed)}\n  axioms: {r.axioms}\n  {r.seconds}s")
    if not r.ok and r.log_tail:
        print(r.log_tail)
    sys.exit(0 if r.ok else 1)


def cmd_repro(a):
    same, ra, rb = repro.compare(Path(a.a), Path(a.b), [Path(f) for f in a.files])
    print(json.dumps({"agree": same, "a": ra, "b": rb}, indent=2))
    sys.exit(0 if same else 1)


def cmd_run(a):
    slug = a.slug
    gate_kw = dict(lake_project=Path(a.lake_project) if a.lake_project else None,
                   paranoid=a.paranoid, strict=a.strict)
    if not (pipeline.problem_dir(slug) / "challenge.lock").exists():
        sys.exit(f"lock the statement first: python -m harness lock {slug} --name ...")
    dupes = pipeline.duplicates(slug)
    if dupes:
        sys.exit(f"duplicate target: {', '.join(dupes)}")
    if not a.skip_eligibility:
        print(f"[0/7] eligibility check (is it still open?)")
        v = pipeline.eligibility(slug, a.agent)
        print(f"   verdict: {v}  (research/{slug}/ELIGIBILITY.md)")
        if v != "open" and not a.force:
            sys.exit("not confirmed open: stopping before spending hunter budget (--force to override)")
    print(f"[1/7] hunting with {a.hunters} x {a.agent}")
    cands = pipeline.hunt(slug, a.agent, a.hunters)
    print(f"   attempts archived in research/{slug}/")
    if not cands:
        sys.exit("no candidates. Nothing to do.")
    for c in cands:
        print(f"[2/7] reproducing {c.name}")
        if not pipeline.reproduce(slug, a.agent, c):
            print("   verifiers disagree: dropped")
            continue
        print(f"[3/7] formalizing {c.name} (gate loop)")
        r = pipeline.formalize(slug, a.agent, c, a.direction, iters=a.iters, **gate_kw)
        if not r.ok:
            print(f"   gate never passed: [{r.failed_layer}] {r.reason}")
            continue
        print("[4/7] prior-art search (again, with the witness)")
        pipeline.prior_art(slug, a.agent, c)
        pv = pipeline.verdict(c / "PRIOR_ART.md")
        print(f"   verdict: {pv}")
        print("[5/7] writeup")
        pipeline.writeup(slug, a.agent, c)
        print("[6/7] adversarial referee")
        rv = pipeline.referee(slug, a.agent, c)
        print(f"   verdict: {rv}")
        out = pipeline.package(slug, c)
        print(f"[7/7] packaged {out.relative_to(ROOT)}")
        if pv != "new" or rv != "accept":
            print(f"   WARNING: prior art = {pv}, referee = {rv}. Do not publish until resolved.")
        print(f"   Now YOU: read Challenge.lean, PRIOR_ART.md and REVIEW.md, then "
              f"`python -m harness approve {slug} --name ...`")
        return
    sys.exit("no candidate survived.")


def cmd_dupes(a):
    hits = pipeline.duplicates(a.slug)
    print("\n".join(hits) if hits else "no duplicates")
    sys.exit(1 if hits else 0)


def cmd_approve(a):
    out = ROOT / "results" / a.slug
    if not (out / "GATE_RECEIPT.json").exists() or not json.loads((out / "GATE_RECEIPT.json").read_text())["ok"]:
        sys.exit("no passing gate receipt in results/; refusing to approve")
    for name, f, good in (("prior art", "PRIOR_ART.md", "new"), ("referee", "REVIEW.md", "accept")):
        v = pipeline.verdict(out / f)
        if v != good:
            print(f"WARNING: {name} verdict is '{v}' (wanted '{good}'). Read {f} before signing.")
    print(open(out / "Challenge.lean").read())
    print("Does the Lean statement above say exactly what the source conjecture says, "
          "and did you check PRIOR_ART.md?  Type 'yes' to sign:")
    if input("> ").strip().lower() != "yes":
        sys.exit("not approved")
    (out / "APPROVAL.md").write_text(
        f"# Human review\n\n- Reviewer: {a.name}\n- Date: {time.strftime('%Y-%m-%d')}\n"
        f"- Statement read and matched to source: yes\n- Prior-art check read: yes\n"
        f"- Challenge sha256: {gate.sha256(out / 'Challenge.lean')}\n")
    pipeline.write_readme(a.slug)
    print("approved.")


def cmd_verify_results(a):
    """Re-run the gate on every packaged result (used by CI)."""
    bad = 0
    for out in sorted((ROOT / "results").glob("*/GATE_RECEIPT.json")):
        slug = out.parent.name
        rec = json.loads(out.read_text())
        prob = pipeline.problem_dir(slug)
        if gate.sha256(out.parent / "Challenge.lean") != gate.sha256(prob / "Challenge.lean"):
            print(f"BAD  {slug}: results/ Challenge.lean differs from problems/"); bad += 1; continue
        r = gate.run_gate(prob, out.parent / "Solution.lean", rec["direction"],
                          lake_project=Path(a.lake_project) if a.lake_project else None)
        print(f"{'ok ' if r.ok else 'BAD'}  {slug}: {'PASS' if r.ok else r.failed_layer + ': ' + r.reason}")
        bad += not r.ok
    sys.exit(1 if bad else 0)


def cmd_status(a):
    slugs = [a.slug] if a.slug else sorted(p.name for p in (ROOT / "runs").glob("*") if p.is_dir())
    for s in slugs:
        print(json.dumps(pipeline.state(s), indent=2))


def main(argv=None):
    p = argparse.ArgumentParser(prog="harness")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("slug"); s.set_defaults(f=cmd_new)
    s = sub.add_parser("lock"); s.add_argument("slug"); s.add_argument("--name", default="unknown"); s.set_defaults(f=cmd_lock)
    for name in ("gate", "run"):
        s = sub.add_parser(name)
        s.add_argument("slug")
        if name == "gate":
            s.add_argument("solution"); s.add_argument("--receipt")
            s.add_argument("--timeout", type=int, default=1800); s.add_argument("--mem-gb", type=int, default=8)
        else:
            s.add_argument("--agent", default="claude"); s.add_argument("--hunters", type=int, default=4)
            s.add_argument("--iters", type=int, default=6)
            s.add_argument("--skip-eligibility", action="store_true")
            s.add_argument("--force", action="store_true", help="hunt even if eligibility is not 'open'")
        s.add_argument("--direction", required=True, choices=["proof", "disproof"])
        s.add_argument("--lake-project"); s.add_argument("--paranoid", action="store_true")
        s.add_argument("--strict", action="store_true", help="warnings in Solution.lean are errors")
        s.set_defaults(f=cmd_gate if name == "gate" else cmd_run)
    s = sub.add_parser("repro"); s.add_argument("a"); s.add_argument("b"); s.add_argument("files", nargs="*"); s.set_defaults(f=cmd_repro)
    s = sub.add_parser("approve"); s.add_argument("slug"); s.add_argument("--name", required=True); s.set_defaults(f=cmd_approve)
    s = sub.add_parser("dupes"); s.add_argument("slug"); s.set_defaults(f=cmd_dupes)
    s = sub.add_parser("verify-results"); s.add_argument("--lake-project"); s.set_defaults(f=cmd_verify_results)
    s = sub.add_parser("status"); s.add_argument("slug", nargs="?"); s.set_defaults(f=cmd_status)
    a = p.parse_args(argv)
    a.f(a)
