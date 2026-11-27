// Independent check of a published counterexample: reads graph6, tests regularity,
// connectivity, finds a small maximal matching and decides exactly whether an
// independent dominating set of size <= K exists (own branch and bound).
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
int n; vector<uint64_t> N, C; long long nodes = 0; vector<int> sol;
// dom = dominated vertices, banned = vertices that may not be chosen, k = picks left
bool ids(uint64_t dom, uint64_t banned, int k) {
  ++nodes;
  uint64_t all = (n == 64) ? ~0ULL : ((1ULL << n) - 1), und = all & ~dom;
  if (!und) return true;
  if (k == 0) return false;
  uint64_t cand = all & ~banned & ~dom;   // independence: never pick a dominated vertex
  int best = -1, bc = 99, mx = 0;
  for (uint64_t u = und; u; u &= u - 1) {
    int v = __builtin_ctzll(u), c = __builtin_popcountll(C[v] & cand);
    if (c < bc) { bc = c; best = v; }
  }
  if (bc == 0) return false;
  for (uint64_t c = cand; c; c &= c - 1) mx = max(mx, __builtin_popcountll(C[__builtin_ctzll(c)] & und));
  if (mx * k < __builtin_popcountll(und)) return false;
  for (uint64_t c = C[best] & cand; c; c &= c - 1) {
    int v = __builtin_ctzll(c);
    sol.push_back(v);
    if (ids(dom | C[v], banned, k - 1)) return true;
    sol.pop_back();
    banned |= 1ULL << v;
  }
  return false;
}
vector<pair<int,int>> E, M;
bool mm(uint64_t used, int k) {            // maximal matching with <= k edges
  for (auto& e : E) if (!(used >> e.first & 1) && !(used >> e.second & 1)) {
    if (!k) return false;
    for (auto& f : E) {
      if ((used >> f.first & 1) || (used >> f.second & 1)) continue;
      if (f.first != e.first && f.first != e.second && f.second != e.first && f.second != e.second) continue;
      M.push_back(f);
      if (mm(used | 1ULL << f.first | 1ULL << f.second, k - 1)) return true;
      M.pop_back();
    }
    return false;
  }
  return true;
}
int main() {
  string s; cin >> s; n = s[0] - 63; N.assign(n, 0); C.assign(n, 0);
  int bit = 0;
  for (int j = 1; j < n; ++j) for (int i = 0; i < j; ++i, ++bit)
    if ((s[1 + bit / 6] - 63) >> (5 - bit % 6) & 1) { N[i] |= 1ULL << j; N[j] |= 1ULL << i; E.push_back({i, j}); }
  for (int v = 0; v < n; ++v) C[v] = N[v] | 1ULL << v;
  int lo = 99, hi = 0; for (int v = 0; v < n; ++v) { int d = __builtin_popcountll(N[v]); lo = min(lo, d); hi = max(hi, d); }
  uint64_t reach = 1; for (int t = 0; t < n; ++t) for (int v = 0; v < n; ++v) if (reach >> v & 1) reach |= N[v];
  cout << "n=" << n << " m=" << E.size() << " degmin=" << lo << " degmax=" << hi << " connected=" << (__builtin_popcountll(reach) == n) << endl;
  // matching lower bound: |M| >= r n / (4r - 2) = 15 for r=3, n=50
  bool ok = mm(0, 15);
  cout << "maximal matching <=15: " << ok << " size=" << M.size() << " :";
  for (auto& e : M) cout << " " << e.first << "-" << e.second; cout << endl;
  for (int K = 15; K <= 16; ++K) {
    nodes = 0; sol.clear(); bool f = ids(0, 0, K);
    cout << "independent dominating set <=" << K << ": " << f << " nodes=" << nodes;
    if (f) { cout << " size=" << sol.size() << " :"; for (int v : sol) cout << " " << v; }
    cout << endl;
  }
}
