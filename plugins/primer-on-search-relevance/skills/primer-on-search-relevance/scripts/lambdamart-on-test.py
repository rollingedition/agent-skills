from lightgbm import LGBMRanker

from lib.metrics import evaluate
from lib.ranking import (DETERMINISTIC, FEATURES, LAMBDARANK, PLANNED_TEST_COMPARISONS, THRESHOLD, TREES, feature_table,
                         fit, ranked, report_planned, stopping_split)
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, train, test = load_products(), load_queries("train"), load_queries("test")
print(f"planned test comparisons: {len(PLANNED_TEST_COMPARISONS)}")
print(f"p-value threshold: {THRESHOLD:.2f}")

table = feature_table(products, train)
table["grade or 0"] = table["grade"].fillna(0).astype(int)            # the setup chosen on train
fit_ids, stop_ids = stopping_split(train.index)
model = fit(LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), table, "grade or 0", FEATURES, fit_ids, stop_ids)
print(f"queries fitted: {len(fit_ids)}\nqueries held out for stopping: {len(stop_ids)}")
curve = model.evals_result_["valid_0"]["ndcg@10"]                     # LightGBM's nDCG@10, one value per tree
print(f"trees tried: {len(curve)}\ntrees kept by early stopping: {model.best_iteration_}")
print(f"stopping queries' ndcg@10, first tree: {curve[0]:.3f}")
print(f"stopping queries' ndcg@10, trees kept: {curve[model.best_iteration_ - 1]:.3f}")
gain = model.booster_.feature_importance(importance_type="gain")      # total gain of the splits on each feature
print(f"features the trees use: {(gain > 0).sum()} of {len(FEATURES)}")
for name, share in sorted(zip(FEATURES, gain / gain.sum()), key=lambda pair: -pair[1]):
    print(f"share of gain, {name}: {share:.3f}")

candidates, judgments = feature_table(products, test), qrels("test")   # test queries: read once, to report
after = evaluate(ranked(candidates, model.predict(candidates[FEATURES])), judgments)
before = evaluate(SemanticSearch().run(test, k=100), judgments)
for name, frame in [("semantic", before), ("lambdamart", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
report_planned("lambdamart", after["ndcg@10"], before["ndcg@10"])
