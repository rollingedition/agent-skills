"""Shows the listwise LLM the same test products in two orders, and measures how far its answers agree and how far each
answer follows the order it was shown. The prose's point rests on the mean tau between the two answers, and on the two
taus between each answer and its own input order."""
import numpy as np
from scipy.stats import kendalltau

from lib.metrics import evaluate
from lib.ranking import DEPTH
from lib.recorded import llm_listwise
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
semantic = SemanticSearch().run(queries, k=DEPTH)               # the order the first prompt showed
answers = llm_listwise().sort_values(["query_id", "order", "position"])
# the products in the order the LLM returned them, for each query and each order shown
answer = {key: list(group["product_id"]) for key, group in answers.groupby(["query_id", "order"])}

def tau(first: list, second: list) -> float:
    """Kendall's tau between two orderings of the same products."""
    place = {product_id: rank for rank, product_id in enumerate(second)}    # each product's place in the second ordering
    # the first ordering's positions, against where the second ordering puts each product
    return kendalltau(range(len(first)), [place[product_id] for product_id in first]).statistic

between, shown_semantic, shown_reversed, overlap, same_first = [], [], [], [], 0
for query_id, shown in semantic.items():
    forward, backward = answer[(query_id, "semantic")], answer[(query_id, "reversed")]
    between.append(tau(forward, backward))
    shown_semantic.append(tau(forward, shown))
    shown_reversed.append(tau(backward, shown[::-1]))     # the reversed input, as the second prompt showed it
    overlap.append(len(set(forward[:10]) & set(backward[:10])))
    same_first += forward[0] == backward[0]               # index 0 is the first place
print(f"test queries: {len(semantic)}")
print(f"tau between the two answers, mean: {np.mean(between):.3f}")
print(f"tau between the two answers, lowest: {min(between):.3f}\ntau between the two answers, highest: {max(between):.3f}")
print(f"top-10 products in common, mean: {np.mean(overlap):.3f}")
print(f"top-10 products in common, fewest: {min(overlap)}")
print(f"queries with the same first product: {same_first}")
print(f"share of queries with the same first product: {same_first / len(semantic):.3f}")
print(f"tau between the order shown and the answer, semantic order: {np.mean(shown_semantic):.3f}")
print(f"tau between the order shown and the answer, reversed order: {np.mean(shown_reversed):.3f}")
# an answer that ignored the order would repeat itself, so its tau with the reversed input is minus its tau with the semantic order
print(f"the same, if the order shown made no difference: {-np.mean(shown_semantic):.3f}")
reversed_run = {query_id: answer[(query_id, "reversed")] for query_id in semantic}
print(f"reversed answer, test ndcg@10, not a planned comparison: {evaluate(reversed_run, judgments)['ndcg@10'].mean():.3f}")
