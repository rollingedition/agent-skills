"""Computes linear weighted kappa by hand for both prompts on the train pool and checks each against scikit-learn. The prose's point rests on the two linear weighted kappa lines, which match scikit-learn's, and on the one-grade-apart shares beside them."""
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from lib.agreement import PROMPTS, graded_pairs

pairs = graded_pairs("train")                     # up to 4 human-judged pairs per label per train query
grades = [2, 1, 0]                                # exact, partial, irrelevant
cost = np.abs(np.subtract.outer(grades, grades)) / 2    # 0 on the diagonal, 0.5 one grade apart, 1 two apart
print("disagreement weights, rows and columns 2, 1, 0")
print(cost)

for prompt in PROMPTS:
    human, llm = pairs["human"].astype(int), pairs[prompt].astype(int)
    # labels fixes the rows and columns to 2, 1, 0 in that order, not the order the grades first appear
    counts = confusion_matrix(human, llm, labels=grades)                       # rows human, columns LLM
    expected = np.outer(counts.sum(axis=1), counts.sum(axis=0)) / counts.sum()   # counts if independent
    weighted = 1 - (cost * counts).sum() / (cost * expected).sum()
    near = cost == 0.5                                                         # cells one grade apart
    print()
    # row 0 is exact and column 2 is irrelevant, so these two corners are the far misses
    print(f"pairs two grades apart, {prompt} prompt: {counts[0, 2] + counts[2, 0]}")
    print(f"disagreements one grade apart, share, {prompt} prompt: {counts[near].sum() / counts[cost > 0].sum():.3f}")
    print(f"one grade apart, share expected by chance, {prompt} prompt: {expected[near].sum() / expected[cost > 0].sum():.3f}")
    print(f"kappa, {prompt} prompt: {cohen_kappa_score(human, llm):.3f}")
    print(f"linear weighted kappa by hand, {prompt} prompt: {weighted:.3f}")
    print(f"linear weighted kappa from scikit-learn, {prompt} prompt: "
          f"{cohen_kappa_score(human, llm, weights='linear'):.3f}")
