"""Sanity check of the blow-up G[mK1]: each vertex -> m non-adjacent copies.
Claim: it is (r*m)-regular, i = m*i(G), mu* <= m*mu*(G).
(1) brute-force i(G[mK1]) == m*i(G) on small random graphs;
(2) on the 48- and 50-vertex counterexamples, check degree and that the blown-up matching is maximal."""
import itertools, random, pathlib
def blow(n, E, m):
    return n*m, [(u*m+a, v*m+b) for u, v in E for a in range(m) for b in range(m)]
def idom(n, E):
    N = [1 << v for v in range(n)]
    for u, v in E: N[u] |= 1 << v; N[v] |= 1 << u
    for k in range(1, n+1):
        for S in itertools.combinations(range(n), k):
            if any(N[u] >> v & 1 for u, v in itertools.combinations(S, 2)): continue
            d = 0
            for v in S: d |= N[v]
            if d == (1 << n) - 1: return k
random.seed(1); trials = 0
for _ in range(300):
    n = random.randint(2, 6); m = random.choice([2, 3])
    E = [e for e in itertools.combinations(range(n), 2) if random.random() < .5]
    assert idom(*blow(n, E, m)) == m*idom(n, E); trials += 1
print("blow-up identity i(G[mK1]) = m*i(G) held in", trials, "random trials")
for f in ["counterexample48.g6", "counterexample.g6"]:
    s = (pathlib.Path(__file__).parent/f).read_text().strip(); n = ord(s[0])-63; E = []; bit = 0
    for j in range(1, n):
        for i in range(j):
            if (ord(s[1+bit//6])-63) >> (5-bit % 6) & 1: E.append((i, j))
            bit += 1
    M = [(2*k, 2*k+1) for k in range(15)]
    for m in (2, 3):
        N_, E_ = blow(n, E, m); deg = [0]*N_
        for u, v in E_: deg[u] += 1; deg[v] += 1
        Mb = [(u*m+a, v*m+a) for u, v in M for a in range(m)]
        used = {x for e in Mb for x in e}; es = {tuple(sorted(e)) for e in E_}
        ok = len(used) == 2*len(Mb) and all(tuple(sorted(e)) in es for e in Mb) and all(u in used or v in used for u, v in E_)
        print(f, "m=%d n=%d degrees=%s maximal_matching=%s size=%d  so mu*<=%d < %d=i" % (m, N_, set(deg), ok, len(Mb), len(Mb), 16*m))
