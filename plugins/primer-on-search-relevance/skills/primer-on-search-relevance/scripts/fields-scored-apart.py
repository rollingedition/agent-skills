from collections import Counter

from lib.lexical_by_hand import InvertedIndex
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products, train = load_products(), load_queries("train")
others = products["product_class"] + ". " + products["category"] + ". " + products["description"]
one_field = InvertedIndex(product_text(products), stem=True)                 # name, class, category, description
name, rest = InvertedIndex(products["name"], stem=True), InvertedIndex(others, stem=True)   # own IDF and lengths

summed = {}
for query_id, query in train["query"].items():
    scores = Counter(name.bm25(query)) + Counter(rest.bm25(query))           # each field saturates on its own
    summed[query_id] = [product_id for product_id, _ in scores.most_common(100)]

runs = {"one field": one_field.run(train), "fields scored apart": summed}
scores = {label: evaluate(run, qrels("train")) for label, run in runs.items()}
for label, frame in scores.items():
    print(f"{label}, train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"{label}, train judged@10: {frame['judged@10'].mean():.3f}")
change = (scores["fields scored apart"]["ndcg@10"] - scores["one field"]["ndcg@10"]).round(3)
print(f"train queries better, worse with fields scored apart: {(change > 0).sum()}, {(change < 0).sum()}")
