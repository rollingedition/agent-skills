import numpy as np
from sklearn.metrics import cohen_kappa_score

from lib.agreement import graded_pairs

pairs = graded_pairs("train")                     # up to 4 human-judged pairs per label per train query
human, llm = pairs["human"].astype(int), pairs["short"].astype(int)
grades = [2, 1, 0]                                # exact, partial, irrelevant
counts = np.array([[((human == row) & (llm == column)).sum() for column in grades] for row in grades])
print("pairs:", counts.sum())
print("rows are the human grades 2, 1, 0 and columns the LLM's, short prompt")
print(counts)

observed = np.trace(counts) / counts.sum()                          # the share of pairs on the diagonal
human_share, llm_share = counts.sum(axis=1) / counts.sum(), counts.sum(axis=0) / counts.sum()
expected = (human_share * llm_share).sum()                          # agreement if the two judged independently
kappa = (observed - expected) / (1 - expected)
print(f"observed agreement, short prompt: {observed:.3f}")
print(f"agreement expected by chance, short prompt: {expected:.3f}")
print(f"kappa by hand, short prompt: {kappa:.3f}")
print(f"kappa from scikit-learn, short prompt: {cohen_kappa_score(human, llm):.3f}")

other = pairs["guidelines"].astype(int)
print(f"observed agreement, guidelines prompt: {(human == other).mean():.3f}")
print(f"kappa from scikit-learn, guidelines prompt: {cohen_kappa_score(human, other):.3f}")
