"""Compares the tuned model's confidence in its supported and made-up answers to the material question, and counts what a
threshold of 0.5 per token keeps. The prose's point rests on the two average confidences and the two threshold counts.
"""
import numpy as np

from lib import claims, recorded

asked = recorded.read("instruction-tuning", "answers")
# only supported and made-up answers are compared; declined and none answers are left out
by_kind = {"supported": [], "made up": []}
for row in asked:
    kind = claims.classify(row["tuned"]["text"], row["description"], row["name"])
    if kind in by_kind:
        # the geometric mean of the token probabilities: exp of their average log-probability
        by_kind[kind].append(np.exp(np.mean(np.log(row["tuned"]["token_probabilities"]))))
for kind, confidence in by_kind.items():
    print(f"tuned model, {kind} answers:", len(confidence))
    print(f"tuned model, {kind} answers, average probability per token:", f"{np.mean(confidence):.2f}")
# a fixed cut for the comparison, not one fitted to these answers
threshold = 0.5
for kind, confidence in by_kind.items():
    print(f"tuned model, {kind} answers above {threshold} per token:", f"{sum(c > threshold for c in confidence)} of {len(confidence)}")
