"""Measures each prompt's agreement with the store's judges on the train pool, as drawn and reweighted to the label mix of all the train judgments. The prose's point rests on the kappa lines for each mix and on the higher-kappa lines, which change with the mix."""
import numpy as np
from sklearn.metrics import cohen_kappa_score

from lib.agreement import LABELS, PROMPTS, graded_pairs
from lib.store import load_labels, load_queries

pairs = graded_pairs("train")                     # drawn evenly: up to 4 pairs per label per train query
drawn = pairs["human"].value_counts(normalize=True)
labels = load_labels()
# every judged label for the train queries, not only the pairs that were drawn
natural = labels[labels["query_id"].isin(load_queries("train").index)]["grade"].value_counts(normalize=True)
top = graded_pairs("test")["human"].dropna().value_counts(normalize=True)    # the rankers' top 10s, judged pairs
for grade, label in LABELS.items():
    print(f"{label} share, as drawn: {drawn[grade]:.3f}")
    print(f"{label} share, in the train judgments: {natural[grade]:.3f}")
    print(f"{label} share, judged test-pool pairs: {top[grade]:.3f}")

# each pair counts for its label's share in the judgments divided by its share as drawn
weight = pairs["human"].map(natural / drawn).astype(float)            # count each pair as if drawn in that mix
kappas = {}
for prompt in PROMPTS:
    human, llm = pairs["human"].astype(int), pairs[prompt].astype(int)
    print()
    print(f"observed agreement, {prompt} prompt, as drawn: {(human == llm).mean():.3f}")
    print(f"kappa, {prompt} prompt, as drawn: {cohen_kappa_score(human, llm):.3f}")
    print(f"observed agreement, {prompt} prompt, train judgments' mix: {np.average(human == llm, weights=weight):.3f}")
    # sample_weight counts each pair that many times; it is not the linear weights of the last section
    kappas[prompt] = cohen_kappa_score(human, llm), cohen_kappa_score(human, llm, sample_weight=weight)
    print(f"kappa, {prompt} prompt, train judgments' mix: {kappas[prompt][1]:.3f}")
print()
for position, mix in enumerate(["as drawn", "train judgments' mix"]):
    # on a tie, max returns the first prompt, short
    print(f"higher kappa, {mix}: {max(PROMPTS, key=lambda prompt: kappas[prompt][position])}")
