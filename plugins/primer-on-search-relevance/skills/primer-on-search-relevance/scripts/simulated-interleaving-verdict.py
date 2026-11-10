import numpy as np
from scipy import stats

from lib.experiments import NAVIGATIONAL, simulate_interleaving
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

for grade, label in [(2, "exact"), (1, "partial"), (0, "irrelevant")]:      # the assumptions, from lib.experiments
    print(f"{label} click probability: {NAVIGATIONAL['click'][grade]}")
    print(f"{label} stop probability: {NAVIGATIONAL['stop'][grade]}")

def ties_reversed(scores):              # BM25's ranking, with equal scores in descending product_id order instead
    return scores.index[np.lexsort((-scores.index.to_numpy(), -scores.to_numpy()))].tolist()


queries, judgments = load_queries("test"), qrels("test")
lexical = LexicalSearch(load_products())
bm25 = lexical.run(queries, k=100)                                        # equal scores by product_id
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([bm25, semantic])
bm25_reversed = {q: ties_reversed(lexical.search(query, k=100)) for q, query in queries["query"].items()}

pairs = {"semantic against bm25": (semantic, bm25), "hybrid against semantic": (hybrid, semantic),
         "hybrid with bm25 ties reversed against semantic": (reciprocal_rank_fusion([bm25_reversed, semantic]), semantic)}
below = {}
for name, (run_a, run_b) in pairs.items():
    outcomes = simulate_interleaving(run_a, run_b, judgments, 10_000, np.random.default_rng(2026))
    for searches in [100, 1_000, 10_000]:
        wins, losses = (outcomes[:searches] == 1).sum(), (outcomes[:searches] == -1).sum()
        p = stats.binomtest(wins, wins + losses).pvalue                  # sign test; ties left out
        below[name, searches] = p < 0.05
        shown = f"{p:.3f}" if p >= 0.001 else "below 0.001"
        print(f"{name}, {searches:,} searches: {wins} wins, {losses} losses, p {shown}")
changes = below["hybrid against semantic", 100] != below["hybrid with bm25 ties reversed against semantic", 100]
print("hybrid against semantic, verdict at 100 searches changes with bm25 ties reversed:", "yes" if changes else "no")
