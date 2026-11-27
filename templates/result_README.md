# {slug}

| | |
|---|---|
| Direction | {direction} |
| Lean gate | {gate} ({layers}) |
| Axioms used | {axioms} |
| Lean | {lean} |
| Human review | {approved} |
| Paper | {pdf} |

**Status:** unrefereed. "Gate passed" means Lean checked that `Solution.lean` proves the
locked statement in `Challenge.lean` using only the standard axioms. It does not mean
the locked statement is the right reading of the source conjecture: that is what
human review is for. See `PRIOR_ART.md` for whether this was already known.

## Files

- `problem.md`: the conjecture and source
- `Challenge.lean` + `challenge.lock`: the locked formal statement (sha256 `{challenge_sha}`)
- `Solution.lean`: the proof (sha256 `{solution_sha}`)
- `GATE_RECEIPT.json`: what the gate checked
- `verify.py`, `verify_independent.py`: two independently written exact checks
- `candidate.json`, `NOTES.md`: the witness and search notes
- `PRIOR_ART.md`: prior-resolution search
- `paper.tex` / `paper.pdf`: the note

## Reproduce

```bash
python3 verify.py && python3 verify_independent.py
python3 -m harness gate {slug} results/{slug}/Solution.lean --direction {direction}
```
