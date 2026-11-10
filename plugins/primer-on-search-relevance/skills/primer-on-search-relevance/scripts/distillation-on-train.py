from lightgbm import LGBMRanker, LGBMRegressor

from lib.metrics import evaluate
from lib.ranking import CHEAP_FEATURES, DETERMINISTIC, LAMBDARANK, TREES, cross_validate, feature_table, ranked
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")          # design work: train queries only
candidates = feature_table(load_products(), queries)
candidates["grade or 0"] = candidates["grade"].fillna(0).astype(int)

student = cross_validate(lambda: LGBMRegressor(**TREES, **DETERMINISTIC), candidates, candidates,
                         "cross_encoder", CHEAP_FEATURES, judgments)          # labels from the teacher
human = cross_validate(lambda: LGBMRanker(**LAMBDARANK, **TREES, **DETERMINISTIC), candidates, candidates,
                       "grade or 0", CHEAP_FEATURES, judgments)               # labels from people
teacher = evaluate(ranked(candidates, candidates["cross_encoder"]), judgments)["ndcg@10"]
semantic = evaluate(SemanticSearch().run(queries, k=100), judgments)["ndcg@10"]
for name, scores in [("semantic", semantic), ("teacher", teacher), ("student, teacher's labels", student),
                     ("lambdarank, human grades, same features", human)]:
    print(f"{name}, train ndcg@10: {scores.mean():.3f}")
result = compare(student, human)
print(f"student minus the human-graded ranker: {result['mean difference']:.3f}")
print(f"student minus the human-graded ranker, permutation p: {result['permutation p']:.3f}")
