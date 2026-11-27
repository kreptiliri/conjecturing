# Orchestrator instructions

You run this repository's research pipeline end to end. The owner's only job is the
final check: they verify finished results in a fresh session (see `VERIFY.md`) and
merge them. Everything before that is yours. Read `README.md` once for the design.

## Ground rules (never break these)

1. **Never edit a locked `Challenge.lean`**, `harness/gate.py`, `harness/lean/`, or
   anything in `tests/` to make a result pass. If the gate rejects, the proof is wrong.
   Gate bugs go in an issue for the owner, never into a result.
2. **Never run `harness approve`.** That signature belongs to the owner.
3. **Never push to `main`.** Results go on a branch `result/<slug>` with a pull request.
   Harness changes go on their own branch and PR, separately from any result.
4. **Never hide a failure.** Dead ends, rejected candidates and "found nothing" are
   committed under `research/<slug>/`. A withdrawn claim is logged in `HISTORY.md`.
5. **Never claim more than was checked.** Label results exactly: complete disproof,
   small-case exception, or partial. Mention what Lean covers and what it does not.

## Setup (once per machine)

- Lean via elan; a Mathlib project at `~/mathproj` (`lake new mathproj math`,
  `lake exe cache get`, `lake build`). Pass it as `--lake-project ~/mathproj`.
- `python3 tests/run_gate_tests.py` must print all cases as expected before any run.
- Agents are configured in `config/agents.toml`. Prefer cheaper agents for
  `eligibility`, `prior_art`, `statement_check`; strongest for `hunter` and `formalizer`.

## Per problem

1. **Pick** a target (or take the one the owner named). Good targets: open, stated in
   google-deepmind/formal-conjectures, recent, computationally checkable. Skip anything
   with a significance line nobody would care about.
2. **Scaffold**: `python3 -m harness new <slug>`. Fill `problem.md` (exact source pinning:
   arXiv id with version, statement number, page). Write `Challenge.lean` with
   `def Challenge.Conjecture : Prop`; copy definitions from formal-conjectures where they
   exist, including their `variable` instance arguments. It must compile against
   `~/mathproj` before anything else.
3. **Statement check**: give `problems/<slug>/` to a *separate* agent with
   `prompts/statement_check.md`. It writes `STATEMENT_CHECK.md` and ticks the boxes.
   On `VERDICT: mismatch`, fix Challenge.lean and repeat with a *fresh* agent. You may
   not tick boxes yourself.
4. **Lock**: `python3 -m harness lock <slug> --name "agent:statement-checker"`.
5. **Run**: `python3 -m harness run <slug> --agent <agent> --hunters 2 --direction disproof --lake-project ~/mathproj`
   (or `--direction proof`). It stops by itself if eligibility is not `open`: accept that.
6. **On success**: the package is in `results/<slug>/`. If prior art is not `new` or
   the referee is not `accept`, fix what the report says (rerun stages) or log it and stop.
   Otherwise: add a `HISTORY.md` entry, commit `problems/<slug>`, `research/<slug>`,
   `results/<slug>` on branch `result/<slug>`, open a PR titled
   `Result: <slug> (<type>)`, and in its body give: the claim in one sentence, the
   witness, scope label, gate receipt hashes, and each verdict.
7. **On failure**: commit `research/<slug>/` with what was searched (ranges, methods),
   on branch `research/<slug>`, PR titled `Attempt: <slug> (no result)`.

## Budget

- `--hunters 2` by default; raise only for a problem with a promising partial result.
- Stop a problem after 2 full runs with no candidate; log the searched ranges.
- Prefer writing one strong search program and letting it run over long agent reasoning.

## When stuck

If the gate rejects in a way that looks like a gate bug (e.g. a Mathlib-mode tooling
error), stop, write the exact error and reproduction to an issue, and move on. Do not
work around the gate.
