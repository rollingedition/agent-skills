from lib.agreement import LABELS, PLANNED, PROMPTS, chapter_one_runs, fill_unjudged, graded_pairs, llm_qrels, planned_verdicts
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels


def order(scores):
    """Rankers by mean nDCG@10 over the test queries, best first."""
    return sorted(scores, key=lambda name: scores[name].mean(), reverse=True)


products, queries, people = load_products(), load_queries("test"), qrels("test")
runs = chapter_one_runs(products, queries)
pairs = graded_pairs("test")                      # every product in the top 10 of the four runs, per test query
unjudged = pairs[pairs["human"].isna()]
print(f"pairs in the test pool: {len(pairs)}\nof them, unjudged: {len(unjudged)}")
for name, run in runs.items():
    missing = sum(product_id not in people[query_id] for query_id, ranking in run.items() for product_id in ranking[:10])
    print(f"unjudged products in the top 10s, {name}: {missing}")
lights = unjudged[unjudged["query_id"] == 133]                             # outdoor light fixtures
print(f"unjudged products for outdoor light fixtures: {len(lights)}\n"
      f"of them, with bulb in the name: {lights['product_id'].map(products['name']).str.contains('bulb').sum()}")
threshold = 0.05 / len(PLANNED)                                            # chapter 3's rule
human = {name: evaluate(run, people)["ndcg@10"] for name, run in runs.items()}            # per-query scores
print(f"order, people's grades only: {' > '.join(order(human))}")

for prompt in PROMPTS:
    counts = ", ".join(str((unjudged[prompt] == grade).sum()) for grade in LABELS)        # grades 2, 1 and 0
    print(f"\nunjudged pairs graded exact, partial, irrelevant, {prompt} prompt: {counts}")
    print(f"unjudged bulbs graded irrelevant, {prompt} prompt: {(lights[prompt] == 0).sum()}")
    filled = {name: evaluate(run, fill_unjudged(people, llm_qrels(prompt)))["ndcg@10"] for name, run in runs.items()}
    print("\n".join(f"{name} ndcg@10, filled by the {prompt} prompt: {filled[name].mean():.3f}" for name in runs))
    print(f"order, filled by the {prompt} prompt: {' > '.join(order(filled))}")
    moved = [name for name, place in zip(order(filled), order(human)) if name != place]
    print(f"rankers that change place when filled, {prompt} prompt: {', '.join(moved) or 'none'}")
    changed = [pair for pair, established in planned_verdicts(filled, threshold).items()
               if established != planned_verdicts(human, threshold)[pair]]
    print(f"verdicts that change when filled, {prompt} prompt: {'; '.join(' minus '.join(pair) for pair in changed) or 'none'}")
