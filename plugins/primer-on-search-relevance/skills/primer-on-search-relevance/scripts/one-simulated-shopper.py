import numpy as np

from lib.experiments import NAVIGATIONAL, cascade_clicks, team_draft
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}
products, queries, judgments = load_products(), load_queries("test"), qrels("test")[246]   # clear shower curtain
semantic = list(SemanticSearch().search(246, k=100).index)
bm25 = list(LexicalSearch(products).search(queries.at[246, "query"], k=100).index)
shown, teams = team_draft(semantic, bm25, np.random.default_rng(7))       # the team-draft example's list
team_names = {"a": "semantic", "b": "bm25"}

rng = np.random.default_rng(2026)
clicks = []
for position, product_id in enumerate(shown):
    grade = judgments.get(product_id, 0)                                  # unjudged counts as 0
    clicked = rng.random() < NAVIGATIONAL["click"][grade]
    leaves = clicked and rng.random() < NAVIGATIONAL["stop"][grade]        # only a click can end the visit
    label = LABELS.get(judgments.get(product_id), "unjudged")
    print(f"{position + 1:>2}  {team_names[teams[position]]:<8}  {label:<10}  {'clicks' if clicked else '':<6}  {'leaves' if leaves else ''}")
    if clicked:
        clicks.append(position)
    if leaves:
        break

credited = [team_names[teams[position]] for position in clicks]       # each click counts for the team that picked it
for_semantic, for_bm25 = credited.count("semantic"), credited.count("bm25")
print("clicks for semantic:", for_semantic)
print("clicks for bm25:", for_bm25)
print("this search goes to:", "semantic" if for_semantic > for_bm25 else "bm25" if for_bm25 > for_semantic else "neither, a tie")
print("same clicks from lib.experiments:", "yes" if cascade_clicks(shown, judgments, np.random.default_rng(2026)) == clicks else "no")
