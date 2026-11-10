from lightgbm import LGBMRanker

from lib.metrics import evaluate
from lib.ranking import DETERMINISTIC, FEATURES, LAMBDARANK, TREE_GRID, TREES, cross_validate, feature_table
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # tuning: train queries only
candidates = feature_table(load_products(), queries)
candidates["grade or 0"] = candidates["grade"].fillna(0).astype(int)  # unjudged counts as irrelevant, as in nDCG
print(f"train queries: {len(queries)}")
print(f"semantic, train ndcg@10: {evaluate(SemanticSearch().run(queries, k=100), judgments)['ndcg@10'].mean():.3f}")

results = {}
for setting in TREE_GRID:                                            # LightGBM's default is 31 leaves at 0.1
    name = f"{setting['num_leaves']} leaves, learning rate {setting['learning_rate']}"
    model = lambda: LGBMRanker(**LAMBDARANK, n_estimators=500, **setting, **DETERMINISTIC)
    results[name] = cross_validate(model, candidates, candidates, "grade or 0", FEATURES, judgments)
    print(f"{name}, cross-validated ndcg@10: {results[name].mean():.3f}")
    print(f"{name}, trees kept per fold: {', '.join(map(str, results[name].attrs['trees']))}")
best = max(results, key=lambda name: results[name].mean())
print(f"settings tried: {len(results)}")
print(f"best setting: {best}")
print(f"lib.ranking.TREES holds it: {'yes' if best == f'{TREES['num_leaves']} leaves, learning rate {TREES['learning_rate']}' else 'no'}")
