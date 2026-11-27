---
slug: euler-41
title: Euler's prime-generating polynomial
source: Folklore (Euler, 1772). Toy problem for testing the harness.
source_url: https://en.wikipedia.org/wiki/Formula_for_primes
area: number theory
expected: disproof
---

# Statement

For every natural number n, the number n² + n + 41 is prime.

# Notes for agents

- Formal statement: `Challenge.lean` in this folder. Do not edit it.
- A counterexample is a single n. A disproof in Lean proves `¬ Challenge.Conjecture`.
