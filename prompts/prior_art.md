# Role: prior-art checker (runs again, right before publishing)

The eligibility check ran before hunting, but other people's agents keep posting.
Check again, now with the actual witness in `candidate.json`.

Search: the source paper's later arXiv versions and errata; papers citing it; the
OEIS; erdosproblems.com; google-deepmind/formal-conjectures; lefttosolve.com; the
Last Math Competition repo; MathOverflow; and the AI-math collections that have
repeatedly published first: PrincipiaMathOrg/math-solutions + mathdb.com,
the-omega-institute/trureturing (issues and PRs), 1337isnot1337/solved-conjectures
(both branches and its issues), and zenodo.org.

Write `PRIOR_ART.md`:
- Every place searched, with links and dates.
- Is the statement still open as stated? Did the authors revise it (e.g. add n ≥ 4)?
- Is this witness, or a smaller or stronger one, already public? By whom, and when?
  Compare the exact hypotheses: a prior result that covers ours (e.g. it works for
  every Q and ours is Q = 2) means ours is not new.
- Verdict, as the last line: `VERDICT: new` | `VERDICT: already known` |
  `VERDICT: statement since revised` | `VERDICT: unclear`

Quote at most one short line per source. Paraphrase the rest. When unsure, say `unclear`.
