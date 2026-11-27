# conjecture-harness

A pipeline for hunting counterexamples and proofs with AI agents, where **no agent is
trusted** and nothing counts until deterministic checks and a human say so.

```
 problem.md + Challenge.lean (locked by you)
        │
  ┌─────▼─────┐   N hunters in parallel, different strategies
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
  │ prior art │── PRIOR_ART.md: is it already known? statement revised?
  └─────┬─────┘
  ┌─────▼─────┐
  │  writeup  │── paper.tex → paper.pdf
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

## Quick start

```bash
# needs python3 >= 3.11 and Lean (elan). Tested with Lean 4.35.0.
python3 tests/run_gate_tests.py                       # gate self-test, ~1 min

python3 -m harness gate euler-41 examples/euler-41/Solution.lean --direction disproof
python3 -m harness run euler-41 --agent fake --hunters 2 --direction disproof   # dry run, no model calls
```

### A real problem

```bash
python3 -m harness new gao-gu-4-12
# 1. problems/gao-gu-4-12/problem.md: exact statement, source, arXiv version
# 2. problems/gao-gu-4-12/Challenge.lean: `def Challenge.Conjecture : Prop := ...`
#    If the problem is in google-deepmind/formal-conjectures, copy its statement.
# 3. READ IT. Check every hypothesis against the paper. Then:
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
runs/<slug>/         agent workspaces, logs, state.json               (gitignored)
results/<slug>/      the publishable package + GATE_RECEIPT.json      (commit these)
harness/             gate.py, pipeline.py, agents.py, repro.py, cli.py
prompts/             one file per role
templates/           paper.tex, result README
tests/               gate self-test, cheats/, fake_agent.py
```

## Publishing

- **Your GitHub:** commit `problems/<slug>` + `results/<slug>`. CI re-runs the self-test
  and re-gates every result on each push.
- **lefttosolve.com:** proofs go in a single file as `OMA.solution` / `OMA.disproof`
  against their pinned formal-conjectures statement. Adapt `Solution.lean` to their
  `join.txt` format before submitting.
- **The Last Math Competition (GitHub):** wants LaTeX + PDF + a Lean project (no sorry,
  no native_decide, no extra axioms) in `solutions/<id>/<you>_submission_<timestamp>/`.
  `results/<slug>/` already has all three.

Label honestly: *complete disproof*, *small-case exception* ("fails only at n = 3"),
or *partial*. Say what the AI did. Don't claim refereeing or priority.

## Status / known gaps

- The core-Lean path is tested end to end here (Lean 4.35.0). The `--lake-project`
  (Mathlib) path is written the same way but hasn't been run against Mathlib yet. Test it
  on one known result before trusting it.
- The lint is a tripwire, not the security boundary. The Lean layers are.
- `paranoid` exports the whole environment; on Mathlib that's gigabytes.
