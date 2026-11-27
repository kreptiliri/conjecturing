"""Command line: python -m harness <command> ...

  new <slug>                      scaffold problems/<slug>/
  lock <slug>                     record Challenge.lean hash (after YOU read it)
  gate <slug> <Solution.lean> --direction proof|disproof [--lake-project DIR] [--paranoid]
  repro <a.py> <b.py> [files...]  compare two verifiers' RESULT lines
  run <slug> --agent claude --hunters 4 --direction disproof
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


def cmd_new(a):
    d = ROOT / "problems" / a.slug
    d.mkdir(parents=True, exist_ok=False)
    (d / "problem.md").write_text(
        f"---\nslug: {a.slug}\ntitle: \nsource: \nsource_url: \narea: \nexpected: unknown\n---\n\n"
        "# Statement\n\n(Exact wording from the source, with version, e.g. arXiv v1, Conjecture 7.3.)\n\n"
        "# Notes for agents\n\n- Formal statement: `Challenge.lean`. Do not edit it.\n")
    (d / "Challenge.lean").write_text(
        "/- Locked statement. Copy from google-deepmind/formal-conjectures when it exists there. -/\n"
        "import Mathlib\n\nnamespace Challenge\n\n/-- The conjecture, as a Prop. -/\n"
        "def Conjecture : Prop := sorry\n\nend Challenge\n")
    print(f"created {d}. Write Challenge.lean, read it carefully, then: python -m harness lock {a.slug}")


def cmd_lock(a):
    d = pipeline.problem_dir(a.slug)
    src = (d / "Challenge.lean").read_text()
    if "sorry" in gate.strip_comments(src):
        sys.exit("Challenge.lean still contains sorry")
    (d / "challenge.lock").write_text(json.dumps({
        "sha256": gate.sha256(d / "Challenge.lean"),
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reviewed_by": a.name}, indent=2) + "\n")
    print(f"locked {a.slug}: {gate.sha256(d / 'Challenge.lean')[:16]}…")


def cmd_gate(a):
    r = gate.run_gate(pipeline.problem_dir(a.slug), Path(a.solution), a.direction,
                      lake_project=Path(a.lake_project) if a.lake_project else None,
                      paranoid=a.paranoid, timeout=a.timeout, mem_gb=a.mem_gb)
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
                   paranoid=a.paranoid)
    print(f"[1/6] hunting with {a.hunters} x {a.agent}")
    cands = pipeline.hunt(slug, a.agent, a.hunters)
    if not cands:
        sys.exit("no candidates. Nothing to do.")
    for c in cands:
        print(f"[2/6] reproducing {c.name}")
        if not pipeline.reproduce(slug, a.agent, c):
            print("   verifiers disagree: dropped")
            continue
        print(f"[3/6] formalizing {c.name} (gate loop)")
        r = pipeline.formalize(slug, a.agent, c, a.direction, iters=a.iters, **gate_kw)
        if not r.ok:
            print(f"   gate never passed: [{r.failed_layer}] {r.reason}")
            continue
        print("[4/6] prior-art search")
        pipeline.prior_art(slug, a.agent, c)
        print("[5/6] writeup")
        pipeline.writeup(slug, a.agent, c)
        out = pipeline.package(slug, c)
        print(f"[6/6] packaged {out.relative_to(ROOT)}. Now YOU: read Challenge.lean + PRIOR_ART.md, "
              f"then `python -m harness approve {slug} --name ...`")
        return
    sys.exit("no candidate survived.")


def cmd_approve(a):
    out = ROOT / "results" / a.slug
    if not (out / "GATE_RECEIPT.json").exists() or not json.loads((out / "GATE_RECEIPT.json").read_text())["ok"]:
        sys.exit("no passing gate receipt in results/; refusing to approve")
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
        s.add_argument("--direction", required=True, choices=["proof", "disproof"])
        s.add_argument("--lake-project"); s.add_argument("--paranoid", action="store_true")
        s.set_defaults(f=cmd_gate if name == "gate" else cmd_run)
    s = sub.add_parser("repro"); s.add_argument("a"); s.add_argument("b"); s.add_argument("files", nargs="*"); s.set_defaults(f=cmd_repro)
    s = sub.add_parser("approve"); s.add_argument("slug"); s.add_argument("--name", required=True); s.set_defaults(f=cmd_approve)
    s = sub.add_parser("verify-results"); s.add_argument("--lake-project"); s.set_defaults(f=cmd_verify_results)
    s = sub.add_parser("status"); s.add_argument("slug", nargs="?"); s.set_defaults(f=cmd_status)
    a = p.parse_args(argv)
    a.f(a)
