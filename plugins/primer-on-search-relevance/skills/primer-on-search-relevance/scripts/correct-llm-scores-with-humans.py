"""Draws random sets of human-judged test queries and corrects the LLM's estimate of two ranker gaps with each set. The prose's point rests on the 'smaller than the human sample's' lines, read with the correlation lines beside them."""
import numpy as np
import pandas as pd

from lib.agreement import PROMPTS, chapter_one_runs, llm_qrels
from lib.metrics import evaluate
from lib.store import load_products, load_queries, qrels

JUDGED, DRAWS = 10, 2000                          # test queries people judge in each draw, and the number of draws
runs = chapter_one_runs(load_products(), load_queries("test"))
people = pd.DataFrame({ranker: evaluate(run, qrels("test"))["ndcg@10"] for ranker, run in runs.items()})
rng = np.random.default_rng(2026)
draws = [rng.choice(people.index, JUDGED, replace=False) for _ in range(DRAWS)]    # which queries people judge
print(f"queries judged by people in each draw: {JUDGED} of {len(people)}\ndraws: {DRAWS:,}")

for after, before in [("semantic", "bm25"), ("hybrid", "semantic")]:
    gap_people = people[after] - people[before]                        # per-query gaps under people's grades
    print(f"\n{after} minus {before}, people, all queries: {gap_people.mean():.3f}")
    # the spread: the standard deviation over the draws, with numpy's default divisor
    alone = np.std([gap_people[judged].mean() for judged in draws])                # the human sample used alone
    print(f"{after} minus {before}, human sample alone, spread: {alone:.3f}")
    for prompt in PROMPTS:
        llm = {ranker: evaluate(run, llm_qrels(prompt))["ndcg@10"] for ranker, run in runs.items()}
        gap_llm, name = llm[after] - llm[before], f"{after} minus {before}, {prompt} prompt"
        # the LLM's mean over all queries, plus the human sample's average of human minus LLM
        corrected = [gap_llm.mean() + (gap_people[judged] - gap_llm[judged]).mean() for judged in draws]
        print(f"{name}, LLM only: {gap_llm.mean():.3f}")
        print(f"{name}, corrected, mean over draws: {np.mean(corrected):.3f}")
        print(f"{name}, corrected, spread: {np.std(corrected):.3f}")
        print(f"{name}, corrected spread smaller than the human sample's: {'yes' if np.std(corrected) < alone else 'no'}")
        # corrcoef returns a 2×2 matrix; [0, 1] is the correlation between the two lists
        print(f"{name}, correlation of per-query gaps with people's: {np.corrcoef(gap_llm, gap_people)[0, 1]:.3f}")
