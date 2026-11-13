import numpy as np

from lib import claims, recorded

asked = recorded.read("instruction-tuning", "answers")
by_kind = {"supported": [], "made up": []}
for row in asked:
    kind = claims.classify(row["tuned"]["text"], row["description"], row["name"])
    if kind in by_kind:
        by_kind[kind].append(np.exp(np.mean(np.log(row["tuned"]["token_probabilities"]))))   # per token, on average
for kind, confidence in by_kind.items():
    print(f"tuned model, {kind} answers:", len(confidence))
    print(f"tuned model, {kind} answers, average probability per token:", f"{np.mean(confidence):.2f}")
threshold = 0.5
for kind, confidence in by_kind.items():
    print(f"tuned model, {kind} answers above {threshold} per token:", f"{sum(c > threshold for c in confidence)} of {len(confidence)}")
