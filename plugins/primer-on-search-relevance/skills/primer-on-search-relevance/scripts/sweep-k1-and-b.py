import pandas as pd

from lib.lexical_by_hand import InvertedIndex, report_test_comparison
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

index = InvertedIndex(product_text(load_products()), stem=True)     # stemmed terms, k1 and b set per search
train, test = load_queries("train"), load_queries("test")
k1_values, b_values = [0.5, 0.9, 1.2, 1.5, 2.0], [0.0, 0.25, 0.5, 0.75, 1.0]


def scores(queries, split, k1, b):
    """One row per query, with BM25 at these parameters."""
    return evaluate(index.run(queries, k1=k1, b=b), qrels(split))


grid = pd.DataFrame({b: {k1: scores(train, "train", k1, b)["ndcg@10"].mean() for k1 in k1_values} for b in b_values})
print("train ndcg@10, k1 down and b across:")
print(grid.round(3).to_string())
best_k1, best_b = grid.stack().idxmax()
print("settings in the grid:", grid.size)
print(f"best k1 on train: {best_k1}")
print(f"best b on train: {best_b}")
edge = best_k1 in (k1_values[0], k1_values[-1]) or best_b in (b_values[0], b_values[-1])
print("best setting on the grid's edge:", "yes" if edge else "no")
print(f"train ndcg@10 at the train best: {grid.at[best_k1, best_b]:.3f}")
print(f"train ndcg@10 at k1 1.5, b 0.75: {grid.at[1.5, 0.75]:.3f}")
print(f"train gain of the best over the defaults: {grid.at[best_k1, best_b] - grid.at[1.5, 0.75]:.3f}")
print(f"lowest train ndcg@10 in the grid: {grid.min().min():.3f}")
print()
runs = {"at k1 1.5, b 0.75": scores(test, "test", 1.5, 0.75), "at the train best": scores(test, "test", best_k1, best_b)}
for name, frame in runs.items():
    print(f"test ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
    print(f"test judged@10 {name}: {frame['judged@10'].mean():.3f}")
report_test_comparison(runs["at the train best"]["ndcg@10"], runs["at k1 1.5, b 0.75"]["ndcg@10"])
