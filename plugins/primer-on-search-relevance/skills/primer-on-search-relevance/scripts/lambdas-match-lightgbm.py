import numpy as np
from lightgbm import LGBMRanker

from lib.ranking import DETERMINISTIC, FEATURES, feature_table
from lib.store import load_products, load_queries

queries = load_queries("train")
one = queries[queries["query"] == "outdoor waterproof chest"]
rows = feature_table(load_products(), one)                  # one query's candidates, in product_id order
grades = rows["grade"].fillna(0).astype(int).to_numpy()
SIGMA = 1.0                                                   # LightGBM's default sigmoid


def lambdas(y_true, y_pred, weight, group):
    """The chapter's lambda for every pair with different grades, as gradients and second derivatives."""
    rank = np.empty(len(y_pred), dtype=int)
    rank[np.argsort(-y_pred, kind="stable")] = np.arange(len(y_pred))   # LightGBM's stable sort on score
    discount, ideal = 1 / np.log2(rank + 2), np.sum(np.sort(y_true)[::-1] / np.log2(np.arange(len(y_true)) + 2))
    gradient, hessian = np.zeros(len(y_pred)), np.zeros(len(y_pred))
    for i in range(len(y_true)):
        for j in np.flatnonzero(y_true < y_true[i]):                      # i should rank above j
            delta = (y_true[i] - y_true[j]) * abs(discount[i] - discount[j]) / ideal
            pull = 1 / (1 + np.exp(SIGMA * (y_pred[i] - y_pred[j])))
            gradient[i], gradient[j] = gradient[i] - SIGMA * pull * delta, gradient[j] + SIGMA * pull * delta
            hessian[[i, j]] += SIGMA ** 2 * pull * (1 - pull) * delta
    return gradient, hessian


tree = {"n_estimators": 5, "num_leaves": 3, "min_child_samples": 5, **DETERMINISTIC}
plain = {"lambdarank_norm": False, "lambdarank_truncation_level": len(rows)}   # LightGBM's lambdas, untouched
models = {"by hand": LGBMRanker(objective=lambdas, **tree),
          "lightgbm, no normalization or truncation": LGBMRanker(objective="lambdarank", label_gain=[0, 1, 2], **plain, **tree),
          "lightgbm at its defaults": LGBMRanker(objective="lambdarank", label_gain=[0, 1, 2], **tree)}
scores = {name: model.fit(rows[FEATURES], grades, group=[len(rows)]).predict(rows[FEATURES], raw_score=True)
          for name, model in models.items()}
print(f"candidates: {len(rows)}")
for name in list(models)[1:]:
    difference = np.abs(scores[name] - scores["by hand"]).max()
    print(f"{name}, largest difference from the lambdas by hand after 5 trees: {difference:.6f}")
