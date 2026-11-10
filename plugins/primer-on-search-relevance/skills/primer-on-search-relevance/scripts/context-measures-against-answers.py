import pandas as pd
from scipy import stats

from lib.generation import context_precision, context_recall, exact_share
from lib.metrics import precision_at_k
from lib.recorded import rag_answers
from lib.store import qrels

judgments = qrels("test")
answers = rag_answers().query("context != 'random'")             # the two retrievers' contexts for each test query
rows = pd.DataFrame([{"recall@5": context_recall(a.context_ids, judgments[a.query_id]),
                      "precision@5": precision_at_k(a.context_ids, judgments[a.query_id], 5),
                      "context precision@5": context_precision(a.context_ids, judgments[a.query_id]),
                      "exact share": exact_share(a.cited, judgments[a.query_id])} for a in answers.itertuples()])
print("contexts:", len(rows))

ranks, spearman = rows.rank(), {}                                # Spearman: Pearson's correlation of the ranks
for measure in ["recall@5", "precision@5", "context precision@5"]:
    spearman[measure] = ranks[measure].corr(ranks["exact share"])
    print(f"spearman with the exact share, {measure}: {spearman[measure]:.3f}")
matches = all(round(value, 9) == round(stats.spearmanr(rows[measure], rows["exact share"]).statistic, 9)
              for measure, value in spearman.items())
print("matches scipy's spearmanr:", "yes" if matches else "no")
print("weakest with the exact share:", min(spearman, key=spearman.get))
