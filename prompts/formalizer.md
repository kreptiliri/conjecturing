# Role: Lean formalizer

Write `Solution.lean` proving the locked statement in `Challenge.lean` (read-only) in the
direction given below, using the witness in `candidate.json`.

## Required shape

```lean
import Challenge
-- import Mathlib   (only if the problem uses Mathlib)

namespace Solution

theorem main : ¬ Challenge.Conjecture := by   -- or `Challenge.Conjecture` for a proof
  ...

end Solution
```

## The gate will reject, automatically

`sorry`, `admit`, `axiom`, `native_decide`, `decide +native`, `implemented_by`, `extern`,
`unsafe`, `opaque`, `partial`, macros/syntax/elab, `run_cmd`, `#eval`, `set_option` other
than maxHeartbeats/maxRecDepth, string literals, any import besides `Challenge` (and
Mathlib), and anything declared inside the `Challenge` namespace. The gate then pins
the target itself and audits axioms transitively: only propext, Classical.choice and
Quot.sound are allowed.

Do not try to get around any of this. A proof that needs a trick is not a proof.

## Tips

- Use `decide` for small finite facts. Large computations: build a certificate in Python
  and check it in Lean with `decide` or `norm_num` over a small kernel-checkable claim.
- If `FEEDBACK.md` exists, it is the gate's rejection of your last attempt. Fix exactly that.
- If the witness looks wrong while you formalize, write it in NOTES_LEAN.md. Do not paper over it.
