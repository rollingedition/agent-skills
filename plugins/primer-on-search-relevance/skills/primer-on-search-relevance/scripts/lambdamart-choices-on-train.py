"""Compares three ways of training on the train queries, each by cross-validation: LambdaRank with unjudged candidates as 0,
LambdaRank on judged candidates only, and pointwise regression. The prose's point rests on the differences and the
permutation p-values printed under each setup."""
from lightgbm import LGBMRanker, LGBMRegressor

from lib.metrics import evaluate
from lib.ranking import DETERMINISTIC, FEATURES, LAMBDARANK, TREES, cross_validate, feature_table
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # tuning: train queries only
candidates = feature_table(load_products(), queries)
candidates["grade or 0"] = candidates["grade"].fillna(0).astype(int)  # unjudged counts as irrelevant
# the rows the model learns from when unjudged candidates are left out; it still ranks every candidate at query time
judged_only = candidates.dropna(subset=["grade"]).astype({"grade": int})

setups = {                                                          # (model, rows it learns from, label)
    "lambdarank, unjudged as 0": (lambda: LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), candidates, "grade or 0"),
    "lambdarank, unjudged left out": (lambda: LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), judged_only, "grade"),
    "pointwise regression, unjudged as 0": (lambda: LGBMRegressor(**TREES, **DETERMINISTIC), candidates, "grade or 0"),
}
semantic = evaluate(SemanticSearch().run(queries, k=100), judgments)["ndcg@10"]
print(f"semantic, train ndcg@10: {semantic.mean():.3f}")
scores = {name: cross_validate(model, rows, candidates, label, FEATURES, judgments)
          for name, (model, rows, label) in setups.items()}
chosen = scores["lambdarank, unjudged as 0"]
for name, per_query in scores.items():
    print(f"{name}, cross-validated ndcg@10: {per_query.mean():.3f}")
    if name != "lambdarank, unjudged as 0":
        # the mean difference is the first argument minus the second, tested by permutation over the queries
        result = compare(per_query, chosen)
        print(f"{name}, minus the first: {result['mean difference']:.3f}")
        print(f"{name}, minus the first, permutation p: {result['permutation p']:.3f}")
result = compare(chosen, semantic)
print(f"first setup minus semantic: {result['mean difference']:.3f}")
print(f"first setup minus semantic, permutation p: {result['permutation p']:.3f}")
