"""Draws the mean difference from 9,999 random sign flips of the hybrid's per-query differences from semantic retrieval, as a histogram, with the observed mean and its mirror marked. The prose's point rests on the observed mean and the p-value by hand, which permutation-test-by-hand prints the same."""
import numpy as np

from lib.figures import ACCENT, MUTED, new_figure, save
from lib.fusion import reciprocal_rank_fusion
from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
semantic = SemanticSearch().run(queries, k=100)
hybrid = reciprocal_rank_fusion([LexicalSearch(load_products()).run(queries, k=100), semantic])
after = evaluate(hybrid, judgments)["ndcg@10"].to_numpy()
before = evaluate(semantic, judgments)["ndcg@10"].to_numpy()
difference = after - before                                       # hybrid minus semantic, per test query
observed = difference.mean()
print(f"observed mean difference: {observed:.3f}")

# the same seed and draws as permutation-test-by-hand, so the same 9,999 sign patterns
rng = np.random.default_rng(2026)
signs = rng.choice([-1, 1], size=(9999, len(difference)))
flipped = (signs * difference).mean(axis=1)                       # 9,999 mean differences under the null hypothesis
print(f"p-value by hand: {np.mean(np.abs(flipped) >= abs(observed)):.3f}")

fig, ax = new_figure(height=3.0)
ax.hist(flipped, bins=60, color=MUTED, linewidth=0, label="mean difference after a random sign flip")
ax.axvline(observed, color=ACCENT, linewidth=1.6, label=f"observed mean, {observed:.3f}")
ax.axvline(-observed, color=ACCENT, linestyle="--", linewidth=1.6, label=f"its mirror, {-observed:.3f}")
ax.set_xlabel("mean hybrid minus semantic nDCG@10 after random sign flips")
ax.set_ylabel("flipped means (of 9,999)")
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False)   # above the plot, clear of both lines
save(fig, "permutation-null")
