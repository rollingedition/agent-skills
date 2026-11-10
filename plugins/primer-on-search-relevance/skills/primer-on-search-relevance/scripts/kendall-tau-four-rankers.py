from itertools import combinations

from scipy.stats import kendalltau

from lib.agreement import chapter_one_runs, llm_qrels
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

products, queries, people = load_products(), load_queries("test"), qrels("test")
runs = chapter_one_runs(products, queries)
short, guidelines = llm_qrels("short"), llm_qrels("guidelines")
pooled = {query_id: {product_id: grade for product_id, grade in people[query_id].items() if product_id in short[query_id]}
          for query_id in people}                 # people's grades for the pairs the LLM judged, and no others
judgment_sets = {"people": people, "people on the LLM's pairs": pooled, "the short prompt": short,
                 "the guidelines prompt": guidelines}
means = {name: {ranker: evaluate(run, judgments)["ndcg@10"].mean() for ranker, run in runs.items()}
         for name, judgments in judgment_sets.items()}
for name, scores in means.items():
    print(f"order under {name}: {' > '.join(sorted(scores, key=scores.get, reverse=True))}")
    for ranker, score in scores.items():
        print(f"{ranker} ndcg@10 under {name}: {score:.3f}")

orders = [sorted(scores, key=scores.get, reverse=True) for scores in means.values()]
steady = [ranker for position, ranker in enumerate(orders[0]) if all(order[position] == ranker for order in orders)]
print(f"rankers in the same place under every set of grades: {', '.join(steady) or 'none'}")
control = means["people on the LLM's pairs"]                              # the same pool, human grades
for name in ["the short prompt", "the guidelines prompt"]:
    print("\n".join(f"{ranker}, {name} minus people on the LLM's pairs: {means[name][ranker] - control[ranker]:+.3f}" for ranker in runs))
pairs, reference = list(combinations(runs, 2)), means["people"]
print(f"\npairs of rankers: {len(pairs)}\nchange in tau from one swapped pair: {2 / len(pairs):.3f}")
for name, scores in list(means.items())[1:]:
    swapped = [(first, second) for first, second in pairs                # discordant: opposite signs
               if (reference[first] - reference[second]) * (scores[first] - scores[second]) < 0]
    print(f"swapped under {name}: {'; '.join(f'{first} and {second}' for first, second in swapped) or 'none'}")
    print(f"tau by hand, people against {name}: {(len(pairs) - 2 * len(swapped)) / len(pairs):.3f}")
    print(f"tau from scipy, people against {name}: {kendalltau(list(reference.values()), list(scores.values())).statistic:.3f}")
