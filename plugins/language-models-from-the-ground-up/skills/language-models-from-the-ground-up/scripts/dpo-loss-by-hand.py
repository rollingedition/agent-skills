import numpy as np

beta = 0.1                                       # how far the tuned model may move from the reference
print("beta:", beta)
# Total log-probabilities of a preferred and a rejected answer to one request, under the model being tuned and under
# the reference model it started from. Made-up numbers, to follow the arithmetic.
cases = {"tuned model favours the preferred answer more than the reference does": (-12.0, -20.0, -14.0, -18.0),
         "tuned model favours it less": (-15.0, -15.0, -14.0, -18.0)}
for label, (preferred, rejected, preferred_reference, rejected_reference) in cases.items():
    margin = beta * ((preferred - preferred_reference) - (rejected - rejected_reference))
    loss = np.log1p(np.exp(-margin))             # -log σ(margin), written so it can't overflow
    print(f"{label}, margin:", f"{margin:.2f}")
    print(f"{label}, loss:", f"{loss:.3f}")
