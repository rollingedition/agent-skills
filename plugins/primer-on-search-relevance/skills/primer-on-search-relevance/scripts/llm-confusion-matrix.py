import pandas as pd
from sklearn.metrics import cohen_kappa_score

from lib.agreement import LABELS, PROMPTS, graded_pairs

order = list(LABELS.values())                     # rows: the store's grades; columns: the LLM's; both exact first
for pool in ["train", "test"]:
    pairs = graded_pairs(pool).dropna(subset=["human"])                    # in the test pool, the pairs people judged
    human = pairs["human"].astype(int)
    print(f"\njudged pairs, {pool} pool: {len(pairs)}\nmean human grade, {pool} pool: {human.mean():.3f}")
    for prompt in PROMPTS:
        llm, name = pairs[prompt].astype(int), f"{pool} pool, {prompt} prompt"
        table = pd.crosstab(human.map(LABELS).rename("human"), llm.map(LABELS).rename(f"llm, {name}"))
        table = table.reindex(index=order, columns=order, fill_value=0)
        errors = {f"{row} called {column}": table.at[row, column] for row in order for column in order if row != column}
        largest = max(errors, key=errors.get)
        print(table)
        print(f"kappa, {name}: {cohen_kappa_score(human, llm):.3f}\nmean llm grade, {name}: {llm.mean():.3f}")
        print(f"llm grade higher than human, {name}: {(llm > human).sum()}")
        print(f"llm grade lower than human, {name}: {(llm < human).sum()}")
        print(f"stricter than the store's judges, {name}: {'yes' if (llm < human).sum() > (llm > human).sum() else 'no'}")
        print(f"largest error, {name}: {largest} ({errors[largest]})")
