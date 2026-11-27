# conjecture-harness

A pipeline for hunting counterexamples and proofs with AI agents, where **no agent is
trusted** and nothing counts until deterministic checks and a human say so.

```
 problem.md + Challenge.lean  →  YOU tick the statement check, then `lock`
        │
  ┌─────▼─────┐   is the exact statement still open? checks papers AND the AI-math
  │eligibility│── collections that keep publishing first. Not "open" → stop, no budget spent
  └─────┬─────┘
  ┌─────▼─────┐   N hunters in parallel, different strategies; every attempt
  │   hunt    │── archived in research/<slug>/ (failures too)
  └─────┬─────┘
  │   hunt    │── candidate.json + verify.py + NOTES.md
  └─────┬─────┘
  ┌─────▼─────┐   a fresh agent that never sees the hunter's code
  │ reproduce │── verify_independent.py; both must print the same RESULT
  └─────┬─────┘
  ┌─────▼─────┐   formalizer writes Solution.lean, gate rejects, feedback, retry
  │ formalize │◄─┐
  └─────┬─────┘  │
  ┌─────▼─────┐  │  CODE, not an agent: lock · lint · compile · pin · axioms ·
  │   GATE    │──┘  recheck · (paranoid)
  └─────┬─────┘
  ┌─────▼─────┐
  │ prior art │── PRIOR_ART.md: checked again, with the witness, right before publishing
  └─────┬─────┘
  ┌─────▼─────┐
  │  writeup  │── paper.tex → paper.pdf
  └─────┬─────┘
  ┌─────▼─────┐   a fresh agent that assumes the note is wrong: statement fidelity,
  │  referee  │── argument, scope, attribution → REVIEW.md
  └─────┬─────┘
  results/<slug>/  →  YOU: `harness approve` (does Challenge.lean mean the conjecture?)
```

## Why the gate is code, not an agent

An agent reviewer can be fooled by the same tricks as the agent that wrote the proof.
The gate trusts only the toolchain, the Challenge.lean that **you** locked, and files it
writes itself:

| Layer | Catches |
|---|---|
| **lock** | Challenge.lean edited after you reviewed it (sha256 in `challenge.lock`) |
| **lint** | `sorry`, `axiom`, `native_decide`, macros, `run_cmd`, `set_option debug…`, extra imports, strings, declarations inside `Challenge.*` |
| **compile** | Solution.lean doesn't build against the *locked* Challenge.lean |
| **pin** | Proving the wrong thing. The gate writes `theorem Gate.pinned : ¬ Challenge.Conjecture := Solution.main` itself |
| **axioms** | Anything beyond `propext`, `Classical.choice`, `Quot.sound`, transitively (sorry, custom axioms, native_decide) |
| **recheck** | Tampered builds: `leanchecker --fresh` re-checks every declaration from the .oleans |
| **paranoid** | Kernel bugs: `leanexport` → `con-leche`, an independent checker (opt-in; slow on Mathlib) |

`tests/run_gate_tests.py` proves the gate does its job. The honest solution passes, and
six cheats (sorry, custom axiom, native_decide, sorry hidden in a macro, a `sorry` helper
lemma, a weakened statement), plus a wrong direction and an edited Challenge.lean, are
each rejected. Every cheat is run twice, **with the lint switched off** the second time,
to show that Lean's own layers catch it too:

```
ok   honest                                     PASS
ok   honest, wrong direction                    rejected at pin
ok   honest, Challenge.lean edited after lock   rejected at lock
ok   custom_axiom (lint OFF)                    rejected at axioms: Solution.euler_fails
ok   macro_sorry (lint OFF)                     rejected at axioms: sorryAx
ok   native_decide (lint OFF)                   rejected at axioms: …native_decide.ax_1_1
ok   weakened (lint OFF)                        rejected at pin
…
15/15 behaved as expected
```

**What the gate can't check:** whether `Challenge.lean` says what the source conjecture
says. That step is yours, and it's where most fake results live. A disproof of a
misread statement is worthless however green the checks are.

## Lessons taken from 1337isnot1337/solved-conjectures

Cinna Davis's collection (200+ results) is the largest public run of this workflow
so far. Its history shows where things go wrong, and the harness is built around that:

- **Priority collisions are the most common failure.** Several entries were withdrawn
  because another AI-math collection (PrincipiaMath/MathDB, the omega-institute
  "trureturing" repo, Zenodo) had already posted the result, sometimes weeks earlier.
  → `eligibility` runs before any hunting, `prior_art` runs again before publishing,
  and both search those collections by name.
- **Statement drift.** Corrections like "every edge must contain at least two vertices"
  were needed after publication. → `problem.md` has a hypothesis-by-hypothesis statement
  check that `lock` refuses to skip, plus exact source pinning (arXiv id + version +
  statement number).
- **Duplicates.** → `harness dupes` matches on source id + statement number, at lock
  and at run time.
- **Breadth over depth.** Her own agent rules now say the collection spent too much on
  narrow targets. → the eligibility report must say who would care, in one line.
- **Failed attempts are data.** → every hunter's notes go to `research/<slug>/`, which
  is committed, so no agent repeats a dead search.
- **Honest labels.** → result type (complete / small-case exception / partial), every
  verdict, and human review are shown in each result's README.

## Quick start

```bash
# needs python3 >= 3.11 and Lean (elan). Tested with Lean 4.35.0.
python3 tests/run_gate_tests.py                       # gate self-test, ~1 min

python3 -m harness gate euler-41 examples/euler-41/Solution.lean --direction disproof
python3 -m harness run euler-41 --agent fake --hunters 2 --direction disproof   # dry run, no model calls
# (the toy is from 1772, so the run ends with a correct "prior art: already known" warning)
```

### A real problem

```bash
python3 -m harness new gao-gu-4-12
# 1. problems/gao-gu-4-12/problem.md: exact statement, source, arXiv version
# 2. problems/gao-gu-4-12/Challenge.lean: `def Challenge.Conjecture : Prop := ...`
#    If the problem is in google-deepmind/formal-conjectures, copy its statement.
# 3. READ IT. Tick the statement check in problem.md, hypothesis by hypothesis. Then:
python3 -m harness lock gao-gu-4-12 --name "Your Name"
python3 -m harness run gao-gu-4-12 --agent claude --hunters 4 --direction disproof \
    --lake-project ~/mathlib-project          # a lake project with Mathlib built
python3 -m harness approve gao-gu-4-12 --name "Your Name"
```

Agents are configured in `config/agents.toml` (Claude Code, Codex, or any CLI). Role
prompts are in `prompts/`. Edit them freely: the gate doesn't care what the agents were told.

### Run untrusted Lean in a container

Building AI-written Lean is running untrusted code. For anything beyond the toy:

```bash
docker build -t harness-lean .
docker run --rm --network none -v "$PWD":/repo -w /repo harness-lean \
  python3 -m harness gate <slug> <Solution.lean> --direction disproof
```

The gate also strips tokens and credentials from the environment before running Lean or Python.

## Layout

```
problems/<slug>/     problem.md, Challenge.lean, challenge.lock      (you write these)
research/<slug>/     ELIGIBILITY.md, ATTEMPTS-*.md                    (commit: failures are data)
runs/<slug>/         agent workspaces, logs, state.json               (gitignored)
results/<slug>/      the publishable package + GATE_RECEIPT.json      (commit these)
harness/             gate.py, pipeline.py, agents.py, repro.py, cli.py
prompts/             one file per role
templates/           paper.tex, result README
tests/               gate self-test, cheats/, fake_agent.py
```

## Adversarial regression coverage

Run `python3 tests/run_gate_tests.py` for 51 checks, including 17 additional cheats
with exact expected rejection layers and two valid syntax controls. Run
`python3 -m unittest discover -s tests -v` for build and pipeline trust-boundary
regressions. See [REVIEW_NOTES.md](REVIEW_NOTES.md) for every trial and result,
the notation-shadowing acceptance bug, and remaining isolation assumptions.
The gate now requires `leanchecker`; elan toolchains are resolved automatically.
Workspace read-only permissions are checked after agents run, but operating-system
isolation is still required to protect canonical files from same-user processes.

## Gate options

`--strict` treats warnings in Solution.lean as errors. `--paranoid` adds the independent
con-leche kernel. `--lake-project DIR` builds against Mathlib from that project.

## Publishing

- **Your GitHub:** commit `problems/<slug>` + `results/<slug>`. CI re-runs the self-test
  and re-gates every result on each push.
- **lefttosolve.com:** proofs go in a single file as `OMA.solution` / `OMA.disproof`
  against their pinned formal-conjectures statement. Adapt `Solution.lean` to their
  `join.txt` format before submitting.
- **The Last Math Competition (GitHub):** wants LaTeX + PDF + a Lean project (no sorry,
  no native_decide, no extra axioms) in `solutions/<id>/<you>_submission_<timestamp>/`.
  `results/<slug>/` already has all three.

Record every publication and every correction in `HISTORY.md`. Withdraw a result
openly if a prior resolution turns up: don't delete it quietly.

Label honestly: *complete disproof*, *small-case exception* ("fails only at n = 3"),
or *partial*. Say what the AI did. Don't claim refereeing or priority.

## Status / known gaps

- The core-Lean path is tested end to end here (Lean 4.35.0). The `--lake-project`
  (Mathlib) path is written the same way but hasn't been run against Mathlib yet. Test it
  on one known result before trusting it.
- The lint is a tripwire, not the security boundary. The Lean layers are.
- `paranoid` exports the whole environment; on Mathlib that's gigabytes.
