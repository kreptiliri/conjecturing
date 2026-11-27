"""Hunter's verifier for euler-41: checks the claimed witness exactly."""
import json


def is_prime(m: int) -> bool:
    if m < 2:
        return False
    d = 2
    while d * d <= m:
        if m % d == 0:
            return False
        d += 1
    return True


n = 40
value = n * n + n + 41
factor = next(d for d in range(2, value) if value % d == 0)
print(f"n={n} value={value} = {factor} * {value // factor}")
print("RESULT " + json.dumps({"witness": {"n": n}, "conjecture_holds_at_witness": is_prime(value)},
                             sort_keys=True))
