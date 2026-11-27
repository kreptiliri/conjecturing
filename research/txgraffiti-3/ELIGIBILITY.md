# Eligibility: txgraffiti-3 (i(G) ≤ μ*(G) for r-regular G, r > 0)

Checked 2026-11-27. All links below were accessed on that date.

## Decision

**The exact statement is false. It was refuted publicly before this run. Do not spend hunting budget on it.**

- A connected cubic graph on 50 vertices with μ* = 15 and i = 16 was posted on 2026-07-23
  ([djma/TxGraffiti-conjecture3-counterexample](https://github.com/djma/TxGraffiti-conjecture3-counterexample),
  commit `7810f30c`, repository created the same day). This is the earliest refutation I found.
- A connected cubic graph on 48 vertices with μ* = 15 and i = 16 followed on 2026-08-24
  ([ipitchford/txgraffiti-order48-successor](https://github.com/ipitchford/txgraffiti-order48-successor),
  [Zenodo 22083656](https://zenodo.org/records/22083656)).
- I checked both graphs with my own exact solver (below). Both hold.
- The statement quantifies over every r ≥ 1, so one cubic graph refutes `Challenge.Conjecture`.
- None of these sources that I read is peer reviewed. The verdict does not rest on their authority:
  it rests on the independent check of the two graphs.

## Independent check

Files are in [verify/](verify/). `verify.cpp` is my own code. It reads graph6, tests regularity and
connectivity, finds a maximal matching, and decides by exhaustive branch and bound whether an
independent dominating set of size ≤ K exists.

| Graph (graph6 file) | n, m | degree | connected | maximal matching found | IDS ≤ 15 | IDS ≤ 16 |
|---|---|---|---|---|---|---|
| `counterexample.g6` (djma graph, copy from ipitchford) | 50, 75 | 3 | yes | 15 edges | none | found |
| `counterexample48.g6` (ipitchford successor) | 48, 72 | 3 | yes | 15 edges | none | found |

So i = 16. Every maximal matching M of a cubic graph satisfies 10·|M| ≥ 3n (counting identity,
[arXiv:2608.22498](https://arxiv.org/abs/2608.22498) Prop. 2), so μ* = 15 in both. Outputs:
`verify_output.txt`, `verify48_output.txt`. The 50-vertex graph6 edge set equals the edge list in
djma's `counterexample.json`.

Run: `c++ -std=c++17 -O3 verify.cpp -o v && ./v < counterexample48.g6`.

## Match to the locked statement

Source and `Challenge.lean` ask: finite simple graph, every degree r, r ≥ 1, then i(G) ≤ μ*(G). No
connectivity. The two graphs are finite, simple, 3-regular. No hypothesis is missed. The "sharp"
clause is irrelevant to a refutation of the inequality.

An external Lean proof of the negation of the formal-conjectures statement exists:
[Solution.lean#L140](https://github.com/danielpuri1901/erdos-lean-formalization/blob/4d006aa2add6f41604be1d143adfc6a645394621/Solution.lean#L140),
with a [checker run](https://github.com/danielpuri1901/erdos-lean-checker/actions/runs/37220457904)
that GitHub reports as `success` (2026-10-04). I did **not** build it or audit its imported certificate
files, and did not compile it against this `Challenge.lean`.

## Which degrees are settled

| r | status of i ≤ μ* | basis |
|---|---|---|
| 1, 2 | true | elementary; source notes the 2-regular case |
| 3 | **false** | graphs above |
| 3m, m ≥ 2 | **false** | blow-up argument below (mine) |
| other r ≥ 4 (4, 5, 7, 8, …) | no public resolution found | see below |

**Blow-up (my derivation; not seen stated in anything I read).** Replace each vertex v of a cubic
counterexample G by m non-adjacent copies, joining copies completely when the originals are adjacent.
The result is 3m-regular and connected. Copies of v have the same neighbourhood, so a maximal
independent set containing one copy contains all of them; hence i = m·i(G) = 16m. For a maximal
matching M of G, matching copy a of u to copy a of w for each uw ∈ M and each a gives a maximal
matching of size m|M|, so μ* ≤ 15m < 16m. Sanity check: `verify/blowup_check.py`
(`blowup_output.txt`): identity on 300 random small graphs; degree and maximal matching for m = 2, 3.

**Sibling and related papers**
- [arXiv:2607.23664](https://arxiv.org/abs/2607.23664) (v1, 2026-07-26): refutes Conjecture 2 (zero
  forcing) only. Nothing on i ≤ μ*.
- [arXiv:2608.22498](https://arxiv.org/abs/2608.22498) (Gupta, v1, 2026-08-23): proves γ ≤ γ_e for
  degree ≥ 7. Remark 1 says this does not give i ≤ γ_e. Partial positive facts it does give: i ≤ μ*
  for degree 3–6 at sufficiently large girth (Section 7); and the proof of Corollary 1 gives
  i ≤ α ≤ n/3 ≤ γ_e whenever α ≤ n/3. Its sentence that the TxGraffiti inequality "is itself open for
  every Δ ≥ 3" is out of date: it does not cite the July or August counterexamples.
- [arXiv:2609.10783](https://arxiv.org/abs/2609.10783) (Afrasyab, v1, 2026-09-09): claims
  γ = 16 > 15 = γ_e on the same 50-vertex graph, which would imply the refutation of i ≤ μ* too. I did
  not check the γ claim.
- [Iwane, Zenodo 22924245](https://zenodo.org/records/22924245) (2026-09-23;
  [code](https://github.com/HirotadaIwane/independent-domination-counterexample), repo created
  2026-07-27): 50-vertex cubic counterexample. Its abstract says the construction extends to k-regular
  graphs for every k ≥ 3, but this is a conditional construction: Problem 17 leaves open whether any
  counterexample of that form exists for k ≥ 4. **It does not settle k ≥ 4.**
- [mateososa48/regular-graph-domination](https://github.com/mateososa48/regular-graph-domination)
  (log dated 2026-11-24): reports no counterexample for degree 3 with n ≤ 20, degree 4 n ≤ 16,
  degree 5 n ≤ 14, degree 6 n ≤ 13 (not rerun); calls degrees 4–6 open. Its degree-6 line is
  superseded by the blow-up above.
- Claw-free regular graphs with r ≥ 2: i ≤ μ* appears to follow from i = γ for claw-free graphs
  (Allan–Laskar, from background knowledge) plus γ ≤ γ_e (Civan et al., as cited by Gupta). Not
  checked against the primary sources.

## Places searched

### 1. Source
| Place | Result |
|---|---|
| [arXiv:2507.17780](https://arxiv.org/abs/2507.17780) | Only v1 (2025-07-23); PDF URLs for v2–v4 return 404. Conjecture 3, §2.3, as locked; says open for r ≥ 3. |
| Web search for journal version / erratum | None found. |
| [DMGT 42 (2022) 921–935](https://www.dmgt.uz.zgora.pl/publish/pdf.php?doi=2317) / [arXiv:1909.09093](https://arxiv.org/abs/1909.09093) | Earlier publication of the same statement as Conjecture 15 ("TxGraffiti 2019"). Journal PDF checked. |
| [RandyRDavila repositories](https://github.com/RandyRDavila) | Only seen in a repository-name search; contents not read. |

### 2. Citing papers and literature
| Place | Result |
|---|---|
| Semantic Scholar citations: [2507.17780](https://api.semanticscholar.org/graph/v1/paper/arXiv:2507.17780/citations) | Empty list on the one successful call; retries rate limited (429). |
| Semantic Scholar citations: 1909.09093, DOI 10.7151/dmgt.2317, 2104.01092, 2608.22498, 2609.10783, 2607.23664 | Lists returned; no proof of i ≤ μ* among titles. 2608.22498 is cited by 2609.10783. |
| [Google Scholar](https://scholar.google.com/scholar?q=%22TxGraffiti%22+%22independent+domination%22+%22maximal+matching%22&as_ylo=2025) | **Not searched**: returned a bot verification page. |
| [OpenAlex](https://api.openalex.org/works?search=%22In%20Reverie%20Together%22) | **Not searched**: daily keyless quota exhausted (429). |
| [arXiv API](https://export.arxiv.org/api/query?search_query=all:TxGraffiti) | Queries: TxGraffiti (12 hits); "independent domination" with "maximal matching" (3), "edge domination" + regular (1), "saturation number" (1). Only relevant refutation: 2609.10783. This is metadata search; arXiv full-text search was not available to me. |
| [arXiv:2608.07956](https://arxiv.org/abs/2608.07956) | Abstract: independent domination and edge colouring; no comparison with maximal matching stated there. |
| General web search | Conjecture wording, both parameter names, "saturation number", "edge domination", 4-regular counterexample, authors + refuted. |

### 3. AI-math collections
| Place | Result |
|---|---|
| [google-deepmind/formal-conjectures 3.lean](https://github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/Arxiv/2507.17780/3.lean) | On `main` still tagged `research open`. Out of date. |
| [issue #6737](https://github.com/google-deepmind/formal-conjectures/issues/6737) (2026-09-30, open) | "Conjecture 3 is false". A commenter reports independently verifying the 48-vertex graph; retag held for the repo's expert-acceptance criterion. |
| [PR #7661](https://github.com/google-deepmind/formal-conjectures/pull/7661) (2026-10-28, open, unmerged) | Negates the statement, links the Lean proof. |
| [PrincipiaMathOrg/math-solutions](https://github.com/PrincipiaMathOrg/math-solutions) | `main` downloaded and grepped, issues and code search: nothing. |
| [mathdb.com](https://mathdb.com/problems/406014) | **Site not readable** (403). Mirror [mathdb-lean/problems 406014](https://github.com/mathdb-lean/problems/tree/main/problems/406014) (export 2026-10-29) shows it open. |
| [the-omega-institute/trureturing](https://github.com/the-omega-institute/trureturing) | Issue/PR and code search (TxGraffiti, 2507.17780, saturation, independent domination, maximal matching): no work on this conjecture; two TxGraffiti mentions are in zero-forcing notes. Other branches not grepped. |
| [1337isnot1337/solved-conjectures](https://github.com/1337isnot1337/solved-conjectures) | `main` and `research` downloaded and grepped, issues searched. `research/campaign-20261121/additional-prior-art.md` records the djma graph as already refuting the regular case. |
| [lefttosolve.com](https://lefttosolve.com/) | **Site did not resolve.** Third-party mirror in [0thernes/unsolved-mathematics](https://github.com/0thernes/unsolved-mathematics) lists it open. |
| [The-Last-Math-Competition](https://github.com/The-Last-Math-Competition/The-Last-Math-Competition) | Code search (TxGraffiti, 2507.17780, saturation number): no hits. |
| [Zenodo](https://zenodo.org/search?q=%22TxGraffiti%22) | Refutations: [21852504](https://zenodo.org/records/21852504) (50 vertices, 2026-08-08), [22083656](https://zenodo.org/records/22083656) (48, 2026-08-24), [22924245](https://zenodo.org/records/22924245) (50, 2026-09-23). Related: [21857209](https://zenodo.org/records/21857209) (cubic with dominating induced matching), [21806398](https://zenodo.org/records/21806398), [21819243](https://zenodo.org/records/21819243), [21934736](https://zenodo.org/records/21934736), [21935386](https://zenodo.org/records/21935386) (descriptions read; none states a result for all r ≥ 4). |
| [Evidence Press release](https://www.evidencepress.org/releases/txgraffiti-c3-resolution/) | 50-vertex candidate, unrefereed; links the 48-vertex successor. |
| Other GitHub finds | [ipitchford 50-vertex](https://github.com/ipitchford/txgraffiti-conjecture3-resolution); [melarKode/txgraffiti-pessimist](https://github.com/melarKode/txgraffiti-pessimist) (June, no counterexample); [senamakel/conjectures-lean](https://github.com/senamakel/conjectures-lean) (records it as disproved); [skyvegetable666/txgraffiti-counterexamples](https://github.com/skyvegetable666/txgraffiti-counterexamples) (a different "Conjecture 3"). |
| [erdosproblems.com](https://www.erdosproblems.com/tags/graph%20theory) | Web search only; no matching entry. |

### 4. OEIS, MathOverflow, Mathlib
| Place | Result |
|---|---|
| [OEIS](https://oeis.org/search?q=TxGraffiti) | Nothing relevant (query for both parameter phrases returned nothing). |
| [MathOverflow](https://mathoverflow.net/search?q=TxGraffiti) and math.SE | Web page blocked (403); Stack Exchange API, four queries per site: nothing relevant. |
| [Mathlib](https://github.com/leanprover-community/mathlib4) | Code search (TxGraffiti, 2507.17780, indepDominationNumber, "independent domination" saturation): no hits. |

## Questions

- **Still open, exactly as stated?** No. False.
- **Direct consequence of a known theorem?** Not of a classical theorem that I know of. It is now a
  direct consequence of public explicit counterexamples.
- **Significance:** domination and matching theorists and the TxGraffiti authors cared (it implies the
  Baste et al. conjecture γ ≤ γ_e for regular graphs), but the answer is already public, so this target
  has no remaining value. A restriction to degrees not divisible by 3 with r ≥ 4 would be a different
  statement and needs its own eligibility check.

VERDICT: resolved
