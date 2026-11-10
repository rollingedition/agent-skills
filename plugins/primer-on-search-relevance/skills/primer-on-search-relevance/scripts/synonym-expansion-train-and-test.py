from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.queries import PLANNED_TEST_COMPARISONS, SYNONYMS, THRESHOLD, expand, report_planned
from lib.store import load_products, load_queries, qrels

products, judgments = load_products(), qrels()
bm25 = LexicalSearch(products)
print("synonym groups:", len(SYNONYMS))
scores = {}
for split in ["train", "test"]:
    queries = load_queries(split)
    expanded = queries.assign(query=queries["query"].map(expand))
    changed = queries.index[expanded["query"] != queries["query"]]
    print(f"{split} queries the list changes:", len(changed))
    for name, frame in [("typed", queries), ("expanded", expanded)]:
        scores[split, name] = evaluate(bm25.run(frame), qrels(split))
        print(f"{split} ndcg@10 {name}: {scores[split, name]['ndcg@10'].mean():.3f}")
        print(f"{split} judged@10 {name}: {scores[split, name]['judged@10'].mean():.3f}")
for query in queries.loc[changed, "query"]:                   # the test queries the list changes
    print(f"test query changed: {query}")
    print(f"words the list adds to it: {expand(query)[len(query) + 1:]}")

change = (scores["train", "expanded"]["ndcg@10"] - scores["train", "typed"]["ndcg@10"]).round(3)
print(f"train queries better, worse: {(change > 0).sum()}, {(change < 0).sum()}")       # for choosing, not evidence
print(f"share of the net train gain from the largest gain: {change.max() / change.sum():.3f}")
for kind, query_id in [("gain", change.idxmax()), ("loss", change.idxmin())]:
    query = load_queries().at[query_id, "query"]
    added = expand(query)[len(query) + 1:]
    print(f"largest train {kind}: {query}")
    print(f"largest train {kind}, words added: {added}")
    print(f"largest train {kind}, change: {change[query_id]:+.3f}")
named = [product_id for product_id in bm25.search(expand(query), k=10).index if added in products.at[product_id, "name"]]
print(f"largest train loss, top 10 names with {added}:", len(named))      # query and added: the largest loss's
print("largest train loss, of those, unjudged:", sum(product_id not in judgments[query_id] for product_id in named))

print("\nplanned test comparisons:", len(PLANNED_TEST_COMPARISONS))
print(f"p-value threshold: {THRESHOLD:.2f}")
report_planned("synonyms, bm25", scores["test", "expanded"]["ndcg@10"], scores["test", "typed"]["ndcg@10"])
