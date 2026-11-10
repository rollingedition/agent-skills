import numpy as np
from lightgbm import LGBMRegressor
from scipy.stats import kendalltau

from lib.metrics import evaluate
from lib.ranking import CHEAP_FEATURES, DETERMINISTIC, TREES, feature_table, fit, ranked, report_planned, stopping_split
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, train, test = load_products(), load_queries("train"), load_queries("test")
table = feature_table(products, train)                       # the teacher's score is the label: no human grades
print(f"train candidates the teacher labels: {len(table)}")
print(f"of them, judged by nobody: {table['grade'].isna().sum()}")
print(f"student features: {len(CHEAP_FEATURES)}")
student = fit(LGBMRegressor(**TREES, **DETERMINISTIC), table, "cross_encoder", CHEAP_FEATURES, *stopping_split(train.index))
print(f"trees kept by early stopping: {student.best_iteration_}")

candidates, judgments = feature_table(products, test), qrels("test")       # test queries: read once, to report
predicted = student.predict(candidates[CHEAP_FEATURES])
gain = student.booster_.feature_importance(importance_type="gain")
for name, share in sorted(zip(CHEAP_FEATURES, gain / gain.sum()), key=lambda pair: -pair[1])[:3]:
    print(f"student's share of gain, {name}: {share:.3f}")
for name in ["cross_encoder", "similarity"]:                   # whose order does the student follow?
    tau = [kendalltau(group[name], predicted[group.index]).statistic for _, group in candidates.groupby("query_id")]
    print(f"tau between student and {name}, mean over test queries: {np.mean(tau):.3f}")
teacher = evaluate(ranked(candidates, candidates["cross_encoder"]), judgments)
print(f"teacher's own order of the candidates, test ndcg@10, not a planned comparison: {teacher['ndcg@10'].mean():.3f}")
after = evaluate(ranked(candidates, predicted), judgments)
before = evaluate(SemanticSearch().run(test, k=100), judgments)
for name, frame in [("semantic", before), ("distilled", after)]:
    print(f"{name}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{name}, test judged@10: {frame['judged@10'].mean():.3f}")
    print(f"{name}, unjudged places in the test top 10s: {round((1 - frame['judged@10']).sum() * 10)}")
report_planned("distilled", after["ndcg@10"], before["ndcg@10"])
