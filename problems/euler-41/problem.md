---
slug: euler-41
title: Euler's prime-generating polynomial
source: Folklore (Euler, 1772). Toy problem for testing the harness.
source_id: toy:euler-41
statement: n^2+n+41 prime
page:
source_url: https://en.wikipedia.org/wiki/Formula_for_primes
area: number theory
expected: disproof
---

# Statement

For every natural number n, the number n² + n + 41 is prime.

# Statement check (fill in before `harness lock`)

- [x] Every hypothesis in the source appears in Challenge.lean, none added
- [x] Domains and objects match: n ranges over all naturals including 0
- [x] Quantifiers and their order match
- [x] Edge cases match: n = 0 gives 41, prime
- [x] Primality defined as: at least 2, only divisors 1 and itself
- [x] Not from formal-conjectures (toy)

# Notes for agents

- Formal statement: `Challenge.lean` in this folder. Do not edit it.
- A counterexample is a single n. A disproof in Lean proves `¬ Challenge.Conjecture`.
