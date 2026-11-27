# Proof checker review

Tested on macOS arm64 with elan and leanprover/lean4:v4.35.0. The initial
review was on `test-coverage` (merged as PR #1); the standalone audit follow-up
is on `standalone-audit`. The original suite passed **15/15** before changes.

## Confirmed acceptance bug and fixes

`case_notation_target.lean` was **ACCEPTED with lint OFF** by the original gate.
It proves only `¬ False`: imported notation changes the parsed occurrence of
`Challenge.Conjecture` in Check.lean. The original axiom audit and pin both pass.
Lint ON already rejected the notation keyword. The repaired audit constructs the
expected kernel expression with explicit `Name.str`/`Expr.const` constructors and
compares it to the compiled Gate.pinned type before collecting axioms. The same
case is now REJECTED at pin with lint OFF. This regression does not rely on lint.

The elan launcher also caused the original gate to silently skip leanchecker:
it searched ~/.elan/bin rather than the toolchain bin directory. Resolve the
prefix using Lean itself and require leanchecker. Missing audit output now fails
closed. The bytes hashed and linted are the bytes compiled, removing separate-read
races for both Challenge and Solution. Tool discovery/version subprocesses are
bounded; execution errors become failed receipts.

The comment scanner now preserves strings and «quoted identifiers» and inserts
whitespace for block comments. Previously `a/- comment -/b` became `ab`, and
`«/-» ... «-/»` swallowed real declarations during lint.

## Lean cases tried

All final cheat files are REJECTED, both with and without lint. EXPECT comments
assert the exact rejection layer for every new case, so an unrelated compilation
failure cannot silently replace the intended test. The original six cases remain.

| File under tests/cheats | Attempt | Lint ON | Lint OFF |
|---|---|---|---|
| `case_attribute_instance.lean` | Reattribute the locked constant as irreducible (Lean requires a local modifier). | REJECTED: lint | REJECTED: compile |
| `case_audit_collision.lean` | Import Audit before the gate builds it. | REJECTED: lint | REJECTED: compile |
| `case_check_collision.lean` | Import Check before the gate builds it. | REJECTED: lint | REJECTED: compile |
| `case_coe_sort.lean` | Use CoeSort to elaborate a wrapper as the proposition True. | REJECTED: pin | REJECTED: pin |
| `case_coercion.lean` | Coerce True into the locked disproof using a sorry-backed instance. | REJECTED: lint | REJECTED: axioms |
| `case_exit_success.lean` | Exit the compiler successfully before defining Solution.main. | REJECTED: lint | REJECTED: pin |
| `case_export_shadow.lean` | Export a false proposition into Challenge and prove its negation. | REJECTED: lint | REJECTED: pin |
| `case_heartbeat.lean` | Run decide with maxHeartbeats = 1; resource failure must reject. | REJECTED: compile | REJECTED: compile |
| `case_nested_comments.lean` | Hide sorry among nested block/documentation comments. | REJECTED: lint | REJECTED: axioms |
| `case_notation_negation.lean` | Override the negation prefix; Lean reports ambiguity in Check. | REJECTED: lint | REJECTED: pin |
| `case_notation_target.lean` | Override the exact token Challenge.Conjecture with notation for False. | REJECTED: lint | REJECTED: pin |
| `case_open_shadow.lean` | Open a namespace containing another Challenge.Conjecture. | REJECTED: pin | REJECTED: pin |
| `case_quoted_comment.lean` | Put comment delimiters inside guillemet identifiers around an axiom. | REJECTED: lint | REJECTED: axioms |
| `case_quoted_namespace.lean` | Extend «Challenge» with a false decoy (bypasses the old namespace regex). | REJECTED: pin | REJECTED: pin |
| `case_simp_attribute.lean` | Rewrite the target using a sorry-backed simp lemma. | REJECTED: lint | REJECTED: axioms |
| `case_unicode_axiom.lean` | Use the Unicode axiom identifier ψ₁. | REJECTED: lint | REJECTED: axioms |
| `case_universe.lean` | Prove ∀ α : Sort u, True, a genuinely universe-polymorphic but different proposition. | REJECTED: pin | REJECTED: pin |
| `custom_axiom.lean` | Original custom axiom. | REJECTED: lint | REJECTED: axioms |
| `fake_lemma.lean` | Original sorry helper. | REJECTED: lint | REJECTED: axioms |
| `macro_sorry.lean` | Original macro-hidden sorry. | REJECTED: lint | REJECTED: axioms |
| `native_decide.lean` | Original compiler-trusting native_decide. | REJECTED: lint | REJECTED: axioms |
| `sorry.lean` | Original direct sorry. | REJECTED: lint | REJECTED: axioms |
| `weakened.lean` | Original different statement. | REJECTED: pin | REJECTED: pin |

Additional trials/controls:

- Honest disproof: PASS; same file in proof direction: REJECTED at pin.
- Challenge weakened after locking: REJECTED at lock.
- `tests/valid/comment_boundaries.lean`: PASS with comment-separated keywords.
- `tests/valid/unicode_nested.lean`: PASS with Unicode helpers, a quoted comment-like
  identifier, and nested documentation comments. These prevent blanket rejection
  from masquerading as stronger coverage.
- Initial universe experiment `{α : Sort u} → α → α`: REJECTED at compile because
  Lean theorems must be propositions. Replaced with the polymorphic Prop above to
  exercise pinning rather than that front-end restriction.
- `case_quoted_comment` originally evaded the custom-axiom lint through the scanner;
  the axiom audit still rejected it. It now rejects at lint too.
- The initial `case_notation_negation` trial was REJECTED at pin (ambiguity), not
  accepted; only notation_target produced a passing invalid receipt.

## Build and orchestration regressions

`tests/test_gate_integration.py` exercises real Lean subprocesses:

- A precompiled false Challenge.olean in a hostile base LEAN_PATH: REJECTED at pin;
  the gate's freshly compiled output directory wins resolution.
- Missing leanchecker with an otherwise working Lean: REJECTED at recheck.
- A successful audit subprocess with no report: REJECTED at axioms.
- Change both source files after hashing but before compilation: the original
  snapshots still compile and PASS, including mandatory recheck; the receipt hashes
  match those original bytes.

`tests/test_regressions.py` exercises the other reviewed modules:

- Verifier RESULT followed by text, duplicate RESULT lines, null/array/empty object,
  duplicate JSON keys, NaN, and a numeric truth flag: REJECTED. Exactly one final
  RESULT object with witness and a real boolean is required.
- Shared file named like the verifier: REJECTED before it can overwrite the script.
- Two verifiers agreeing the conjecture holds: reproduction returns false.
- Two verifiers agreeing on a different witness: reproduction returns false.
- Duplicate/conflicting verdicts, fenced verdicts, malformed verdicts and unknown
  verdict values: parsed as missing. One standalone allowed verdict is required.
- Existing successful report in a reused workspace: removed before the next run.
- Same-user deletion/replacement of a mode-0444 Challenge: detected, restored, exit
  125. Making Challenge writable also returns 125 and restores mode 0444.
- Failed/crashed/timed-out agents (including exit 125): pipeline refuses artifacts.
- Simulated Lean timeout, signal crash and missing executable: GateFail, never PASS.
- Unterminated comment: lint failure; quoted delimiters and token spacing preserved.

## Limits and remaining trust assumptions

Agreement of Python programs cannot establish mathematical correctness or genuine
independence: both can print the same fabricated false result, or share an algorithm
bug. Matching schemas and the candidate witness only filter obvious false agreement;
Lean remains the proof boundary. The reproducer does not receive hunter code, but
same-user processes can read outside their working directories. `python -I` is not
a sandbox.

Mode 0444 is advisory, not an OS-enforced read-only mount. The new agent checks detect
persistent edits and permission changes; a process can modify then restore a file,
spawn descendants, or access canonical repository files as the same user. The gate
uses the canonical hash-locked snapshot rather than trusting workspace Challenge.
Protect the canonical Challenge **and lock** from untrusted processes with a read-only
container mount/separate identity. If the agent can edit both trusted files or the
harness/toolchain, hashes do not create a security boundary. No Python/Lean source
filter is a substitute for process isolation. Lint OFF is adversarial test mode,
not permission to run arbitrary metaprograms on an unprotected host.

Mathlib/lake and optional con-leche were reviewed statically but not exercised here;
this review does not claim complete coverage of arbitrary imported plugins or kernel
bugs. Pin type comparison intentionally requires the exact locked constant/type.

## Validation

- Original `python3 tests/run_gate_tests.py`: **15/15**.
- Expanded `python3 tests/run_gate_tests.py`: **51/51** (17 new cheats, each twice,
  plus two honest syntax controls).
- `python3 -m unittest discover -s tests -v`: **14 tests**, including four real Lean
  build-boundary tests.
- `python3 -m harness run euler-41 --agent fake --hunters 2 --direction disproof`:
  completed through reproduction, Lean recheck and packaging; correctly warned that
  the toy is already known. Generated research/results are excluded from this PR.
- CI runs both the expanded gate suite and the regression suite.


## Standalone audit follow-up

The old Audit.lean imported Check and therefore Solution before elaborating its
own audit code. Imported instances and macros could change that code. The new
`harness/lean/AuditMain.lean` imports only Lean and runs with `lean --run`.
At runtime it loads Check with `Lean.importModules` and `loadExts := false`;
Solution declarations are inspected as data, without running their initializers
or activating their environment extensions. `Lean.collectAxioms` traverses the
loaded environment without relying on imported extension caches.

The expected proof/disproof type is constructed explicitly and compared using
`Lean.Expr.equal`. Axiom membership uses `Lean.Name.beq` against exactly propext,
Classical.choice and Quot.sound. Neither comparison selects a BEq instance.
Check still imports only Challenge and Solution, so mandatory
`leanchecker --fresh Check` does not acquire an audit dependency on Lean.

Each invocation receives a fresh 256-bit random token. AuditMain emits one JSON
report carrying the token, status and axiom list. Acceptance requires exit zero,
exactly one valid report, the matching token, and status `ok`. Nonzero exit,
missing/duplicate reports, wrong tokens, and failure statuses fail closed.
The token binds a report to this run; process isolation assumptions above still
apply to untrusted same-user metaprograms.

New regressions (each also checked with lint ON):

| File under tests/cheats | Attempt | Lint OFF |
|---|---|---|
| `case_beq_name.lean` | Always-true BEq Lean.Name plus a custom axiom. | REJECTED: axioms |
| `case_beq_expr.lean` | Always-true BEq Lean.Expr plus a notation-substituted false target. | REJECTED: pin |
| `case_macro_run_cmd.lean` | Replace run_cmd with a forged empty axiom report. | REJECTED: axioms |

Validation after refactoring:

- `python3 tests/run_gate_tests.py`: **57/57**, retaining all 51 existing cases.
- Regression suites: **16 tests passed** (11 Python regressions and five real
  Lean integration tests), including exit status and token-protocol checks.
- A real Lean initializer writes a marker during compilation; running AuditMain
  leaves that marker unchanged and the honest solution passes through recheck.
- CI initializes Lean with `lean --version` before starting concurrent tests.
  PR #1's CI failures came from concurrent first-use elan installation and its
  diagnostics contaminating toolchain-prefix discovery.
