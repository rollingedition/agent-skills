"""Adds a bonus for each adjacent pair of query terms that appears in order in a product's name, picks the bonus on train and checks it on test. The prose's point rests on the test permutation p line and the test nDCG@10 lines."""
from lib.lexical_by_hand import InvertedIndex, PositionalIndex, report_test_comparison, tokenize
from lib.metrics import evaluate
from lib.store import load_products, load_queries, product_text, qrels

products = load_products()
index = InvertedIndex(product_text(products), stem=True)
names = PositionalIndex(products["name"], stem=True)      # the positions phrase-positions-by-hand builds


def with_bonus(split, bonus):
    """BM25's top 100, plus the bonus for each pair of adjacent query terms found, in order, in the name."""
    run = {}
    for query_id, query in load_queries(split)["query"].items():
        terms, scores = tokenize(query, stem=True), index.search(query)
        pairs = list(zip(terms, terms[1:]))
        # only BM25's top 100 get a bonus, so it reorders them and adds no product
        scores += [bonus * sum(names.has_phrase(product_id, list(pair)) for pair in pairs) for product_id in scores.index]
        run[query_id] = list(scores.sort_values(ascending=False, kind="stable").index)
    return evaluate(run, qrels(split))


train_scores = {bonus: with_bonus("train", bonus) for bonus in [0, 0.5, 1, 2]}
for bonus, frame in train_scores.items():
    print(f"bonus {bonus}, train ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"bonus {bonus}, train judged@10: {frame['judged@10'].mean():.3f}")
best = max(train_scores, key=lambda bonus: train_scores[bonus]["ndcg@10"].mean())
print("best bonus on train:", best)
print()
# the defaults, with no bonus, and the best bonus on train
test_scores = {bonus: with_bonus("test", bonus) for bonus in [0, best]}
for bonus, frame in test_scores.items():
    print(f"bonus {bonus}, test ndcg@10: {frame['ndcg@10'].mean():.3f}")
    print(f"bonus {bonus}, test judged@10: {frame['judged@10'].mean():.3f}")
# the planned test comparison: permutation test, t-test and bootstrap interval
report_test_comparison(test_scores[best]["ndcg@10"], test_scores[0]["ndcg@10"])
