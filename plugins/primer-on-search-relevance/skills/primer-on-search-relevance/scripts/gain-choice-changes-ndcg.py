from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(load_products()).run(queries, k=100), "semantic": SemanticSearch().run(queries, k=100)}

for name, run in runs.items():
    grades = [judgments[query_id].get(product_id) for query_id, ranking in run.items() for product_id in ranking[:10]]
    print(f"partial share of the {name} top 10: {grades.count(1) / len(grades):.3f}")

schemes = {"exact only": {2: 1, 1: 0, 0: 0},
           "exact or partial": {2: 1, 1: 1, 0: 0},
           "grades 2, 1, 0": {2: 2, 1: 1, 0: 0},       # the book's choice; WANDS's 1, 0.5, 0 gives the same nDCG
           "partial gain 0.1": {2: 1, 1: 0.1, 0: 0}}   # close to the gains ESCI chose for its substitutes
leads = 0
for scheme, gain in schemes.items():
    gains = {query_id: {product_id: gain[grade] for product_id, grade in per_query.items()}
             for query_id, per_query in judgments.items()}
    scores = {name: evaluate(run, gains)["ndcg@10"] for name, run in runs.items()}
    test = compare(scores["semantic"], scores["bm25"])  # exploratory paired tests (chapter 3): no planned comparisons
    print(f"bm25, {scheme}: {scores['bm25'].mean():.3f}")
    print(f"semantic, {scheme}: {scores['semantic'].mean():.3f}")
    print(f"semantic minus bm25, {scheme}: {test['mean difference']:.3f}")
    print(f"permutation p, {scheme}: {test['permutation p']:.3f}")
    print(f"t-test p, {scheme}: {test['t-test p']:.3f}")
    print(f"tied queries, {scheme}: {test['ties']}")
    leads += test["mean difference"] > 0
print(f"schemes where semantic leads: {leads} of {len(schemes)}")
