from lib.lexical_by_hand import InvertedIndex, report_test_comparison, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products = load_products()
text = product_text(products)
with_attributes = text + ". " + products["attributes"]      # names and values, one more field, weight 1

exact = [product_id for product_id, grade in qrels("test")[246].items() if grade == 2]    # clear shower curtain
print("exact products for query 246:", len(exact))
print("exact, with clear in their text:", sum("clear" in tokenize(text[product_id]) for product_id in exact))
print("exact, with clear in text or attributes:", sum("clear" in tokenize(with_attributes[product_id]) for product_id in exact))
found = next(product_id for product_id in exact
             if "clear" in tokenize(products.at[product_id, "attributes"]) and "clear" not in tokenize(text[product_id]))
print(f"for example: {products.at[found, 'name']} -> {products.at[found, 'attributes']}")
names = {"color", "material", "style", "finish", "shape", "size", "width", "height", "depth"}       # the attribute names
print("queries that contain an attribute name:", load_queries()["query"].map(lambda query: bool(names & set(tokenize(query)))).sum())
print("products whose attributes name size:", sum("size" in tokenize(value) for value in products["attributes"]))

indexes = {"one field": InvertedIndex(text, stem=True), "with attributes": InvertedIndex(with_attributes, stem=True)}
scores = {split: {label: evaluate(index.run(load_queries(split)), qrels(split)) for label, index in indexes.items()}
          for split in ["train", "test"]}           # one candidate, fixed in advance: tuned on nothing
for split in ["train", "test"]:
    print()
    for label, frame in scores[split].items():
        print(f"{split} ndcg@10, {label}: {frame['ndcg@10'].mean():.3f}")
        print(f"{split} judged@10, {label}: {frame['judged@10'].mean():.3f}")
print()
for query_id in [246, 58]:                       # clear shower curtain, medium size chandelier: test queries
    for label, frame in scores["test"].items():
        print(f"query {query_id} ndcg@10, {label}: {frame.at[query_id, 'ndcg@10']:.3f}")
report_test_comparison(scores["test"]["with attributes"]["ndcg@10"], scores["test"]["one field"]["ndcg@10"])
