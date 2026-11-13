"""Works out LambdaRank's λ for every pair in one train query's top 10 by hand, and checks each pair's |ΔnDCG| against
swapping the pair in the metric. The prose's point rests on the strongest push up and down, and on the count of pairs
whose formula matches swapping."""
import math
from itertools import combinations

from lib.metrics import dcg_at_k, ndcg_at_k
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

queries, judgments = load_queries("train"), qrels("train")
query_id = queries.index[queries["query"] == "outdoor waterproof chest"][0]
judged = judgments[query_id]
scores = SemanticSearch().search(query_id, k=10)       # the model so far: semantic similarity
ranking, similarity = list(scores.index), scores.to_numpy()
# an unjudged product counts as grade 0, as it does in the metric
grades = [judged.get(product_id, 0) for product_id in ranking]
# the ideal DCG takes every judged product, as lib.metrics does; sigma is 1, LightGBM's default sigmoid
ideal, sigma = dcg_at_k(sorted(judged.values(), reverse=True), 10), 1.0
print("grades from the top:", " ".join(map(str, grades)))

force, checks, pulls = [0.0] * len(ranking), [], []
for i, j in combinations(range(len(ranking)), 2):      # i is above j
    if grades[i] == grades[j]:
        continue
    better, worse = (i, j) if grades[i] > grades[j] else (j, i)
    ranknet = 1 / (1 + math.exp(sigma * (similarity[better] - similarity[worse])))      # RankNet's pull
    # i and j count from 0, so position p is i + 1 and its discount is 1 / log2(p + 1), which is 1 / log2(i + 2)
    delta = abs((grades[i] - grades[j]) * (1 / math.log2(i + 2) - 1 / math.log2(j + 2))) / ideal
    swapped = ranking.copy()
    swapped[i], swapped[j] = swapped[j], swapped[i]
    checks.append(math.isclose(delta, abs(ndcg_at_k(swapped, judged, 10) - ndcg_at_k(ranking, judged, 10))))
    pulls.append(ranknet)
    pair_lambda = sigma * ranknet * delta                         # LambdaRank: scaled by |delta nDCG|
    force[better], force[worse] = force[better] + pair_lambda, force[worse] - pair_lambda

print(f"pairs with different grades: {len(checks)}")
print(f"pairs where delta ndcg by formula matches swapping the pair: {sum(checks)}")
for position, push in enumerate(force, start=1):
    print(f"force at position {position}: {push:+.3f}")
# list indexes count from 0 and positions from 1, hence the + 1
print(f"strongest push up, position: {force.index(max(force)) + 1}")
print(f"strongest push down, position: {force.index(min(force)) + 1}")
print(f"ranknet's pull, lowest: {min(pulls):.3f}\nranknet's pull, highest: {max(pulls):.3f}")
