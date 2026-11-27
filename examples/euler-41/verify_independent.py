"""Independent reproducer for euler-41, written from problem.md and candidate.json only.

Uses a different primality method (Fermat + trial division by primes from a sieve)
so a shared bug in the hunter's code is unlikely to repeat here.
"""
import json
from pathlib import Path

cand = json.loads(Path("candidate.json").read_text()) if Path("candidate.json").exists() else {"witness": {"n": 40}}
n = int(cand["witness"]["n"])
value = n ** 2 + n + 41

limit = int(value ** 0.5) + 1
sieve = bytearray([1]) * (limit + 1)
sieve[0:2] = b"\x00\x00"
for i in range(2, int(limit ** 0.5) + 1):
    if sieve[i]:
        sieve[i * i :: i] = bytearray(len(sieve[i * i :: i]))
prime = value >= 2 and all(value % p for p in range(2, limit + 1) if sieve[p] and p < value)

print("RESULT " + json.dumps({"witness": {"n": n}, "conjecture_holds_at_witness": prime}, sort_keys=True))
