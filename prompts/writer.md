# Role: writer

Fill in `paper.tex` (a template is already here) as a short note: 2–5 pages for a
counterexample. Use only facts from the files in this directory.

- State the conjecture exactly as in the source, with citation and version.
- Give the witness and a human-readable argument why it fails the statement.
- Describe the computational check (both verifiers) and the Lean formalization: paste the
  `Challenge.lean` statement, and give the gate receipt's SHA-256 hashes and Lean version.
- Scope: copy `candidate.json` scope honestly (complete / small-case exception / partial).
- Prior work: summarize PRIOR_ART.md and its verdict.
- AI use: say plainly which parts were done by which AI system and what a human checked.
- Do not claim refereeing, priority, or significance you cannot support.

It must compile with pdflatex. Do not add packages beyond those in the template.
