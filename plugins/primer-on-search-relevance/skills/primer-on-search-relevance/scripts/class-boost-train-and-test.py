from lib.metrics import evaluate
from lib.queries import THRESHOLD, class_boost_run, in_class, report_planned, train_classifier
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

products, queries = load_products(), load_queries()
vectorizer, model = train_classifier(products)               # trained on product text, never on queries
predicted = dict(zip(queries.index, model.predict(vectorizer.transform(queries["query"]))))
semantic = SemanticSearch()
train, train_judgments = load_queries("train"), qrels("train")

exact, outside = 0, 0
for query_id, judged in train_judgments.items():
    member = in_class(products, predicted[query_id])
    exact += sum(grade == 2 for grade in judged.values())
    outside += sum(grade == 2 and not member[product_id] for product_id, grade in judged.items())
print(f"exact train products outside the predicted class: {outside} of {exact}")

base = evaluate(semantic.run(train), train_judgments)
print(f"train ndcg@10 semantic: {base['ndcg@10'].mean():.3f}")
print(f"train judged@10 semantic: {base['judged@10'].mean():.3f}")
train_scores = {}
for weight in [None, 0.01, 0.02, 0.05, 0.1, 0.2]:                          # None: keep only the predicted class
    train_scores[weight] = evaluate(class_boost_run(semantic, train.index, predicted, products, weight), train_judgments)
    name = "filter" if weight is None else f"boost {weight}"
    print(f"train ndcg@10 {name}: {train_scores[weight]['ndcg@10'].mean():.3f}")
boosts = [weight for weight in train_scores if weight is not None]
best = max(boosts, key=lambda weight: train_scores[weight]["ndcg@10"].mean())
for name, weight in [("filter", None), ("best boost", best)]:
    print(f"train judged@10 {name}: {train_scores[weight]['judged@10'].mean():.3f}")
print("best boost on train:", best)

print(f"\nthe planned test comparison, threshold {THRESHOLD:.2f}:")
test, test_judgments = load_queries("test"), qrels("test")
boosted = evaluate(class_boost_run(semantic, test.index, predicted, products, best), test_judgments)
plain = evaluate(semantic.run(test), test_judgments)
print(f"test judged@10 semantic: {plain['judged@10'].mean():.3f}")
print(f"test judged@10 boosted: {boosted['judged@10'].mean():.3f}")
report_planned("class boost, semantic", boosted["ndcg@10"], plain["ndcg@10"])
