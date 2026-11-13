"""Repeats the product name in the indexed text, once per extra weight, and picks the weight with the best train nDCG@10 for the test comparison. The prose's point rests on the best-weight line and the test permutation p line."""
from lib.lexical_by_hand import InvertedIndex, report_test_comparison
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, train, test = load_products(), load_queries("train"), load_queries("test")
# product_text already holds the name once, so weight - 1 more copies make it weight in all
indexes = {weight: InvertedIndex((products["name"] + ". ") * (weight - 1) + product_text(products), stem=True)
           for weight in [1, 2, 3, 5]}            # BM25F with whole-number weights: the name counted weight times

train_scores = {weight: evaluate(index.run(train), qrels("train")) for weight, index in indexes.items()}
for weight, frame in train_scores.items():
    print(f"name weight {weight}, train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"name weight {weight}, train judged@10: {frame['judged@10'].mean():.3f}")
# on a tie, max keeps the first weight, the smaller one
best = max(train_scores, key=lambda weight: train_scores[weight]["ndcg@10"].mean())
print("best name weight on train:", best)
print()
runs = {"one field": indexes[1].run(test), "best name weight": indexes[best].run(test)}
scores = {label: evaluate(run, qrels("test")) for label, run in runs.items()}
for label, frame in scores.items():
    print(f"{label}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{label}, test judged@10: {frame['judged@10'].mean():.3f}")
# the planned test comparison: permutation test, t-test and bootstrap interval
report_test_comparison(scores["best name weight"]["ndcg@10"], scores["one field"]["ndcg@10"])
