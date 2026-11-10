from lib.lexical_by_hand import THRESHOLD, InvertedIndex, report_test_comparison
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

text = product_text(load_products())
indexes = {"without stemming": InvertedIndex(text), "with stemming": InvertedIndex(text, stem=True)}
scores = {split: {name: evaluate(index.run(load_queries(split)), qrels(split)) for name, index in indexes.items()}
          for split in ["train", "test"]}

for split in ["train", "test"]:
    for name, frame in scores[split].items():
        print(f"{split} ndcg@10 {name}: {frame['ndcg@10'].mean():.3f}")
        print(f"{split} judged@10 {name}: {frame['judged@10'].mean():.3f}")
change = (scores["train"]["with stemming"]["ndcg@10"] - scores["train"]["without stemming"]["ndcg@10"]).round(3)
print(f"train queries better, worse: {(change > 0).sum()}, {(change < 0).sum()}")    # for choosing, not evidence
for query_id in [410, 359]:                       # pool floats and french molding, train queries
    for name, frame in scores["train"].items():
        print(f"query {query_id} {name}: {frame.at[query_id, 'ndcg@10']:.3f}")

print(f"\nthe planned test comparison, threshold {THRESHOLD:.2f}:")
after, before = scores["test"]["with stemming"]["ndcg@10"], scores["test"]["without stemming"]["ndcg@10"]
report_test_comparison(after, before)
gain = after - before
print("test query with the largest gain:", gain.idxmax())
print(f"its gain: {gain.max():.3f}")
print(f"mean test gain without it: {gain.drop(gain.idxmax()).mean():.3f}")
