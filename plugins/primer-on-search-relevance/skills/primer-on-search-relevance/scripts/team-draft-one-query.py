"""Team draft over one query's semantic and BM25 rankings: the interleaved list, and the team that picked each place. The prose's point rests on the BM25 pick at the bottom of the list, and on the 'same list' line that checks lib.experiments."""
import numpy as np

from lib import experiments
from lib.lexical import LexicalSearch
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, qrels

LABELS = {2: "exact", 1: "partial", 0: "irrelevant"}


def team_draft(ranking_a, ranking_b, rng, length=10):
    """Like picking teams: the team with fewer picks goes next, a coin flip decides when they're level,
    and each team adds its best product that isn't shown yet."""
    shown, teams = [], []
    while len(shown) < length:
        picks_a, picks_b = teams.count("a"), teams.count("b")
        # the coin is drawn only when the teams are level
        a_picks = picks_a < picks_b or (picks_a == picks_b and rng.random() < 0.5)
        ranking, team = (ranking_a, "a") if a_picks else (ranking_b, "b")
        # the team's best product that isn't shown yet, from its own ranking
        shown.append(next(p for p in ranking if p not in shown))
        teams.append(team)
    return shown, teams


products, queries, judgments = load_products(), load_queries("test"), qrels("test")[246]   # clear shower curtain
semantic = list(SemanticSearch().search(246, k=100).index)
bm25 = list(LexicalSearch(products).search(queries.at[246, "query"], k=100).index)

shown, teams = team_draft(semantic, bm25, np.random.default_rng(7))
# judgments.get returns None for a product nobody judged, and LABELS.get then gives 'unjudged'
# names are cut at 45 characters to keep the columns aligned
for position, (product_id, team) in enumerate(zip(shown, teams), start=1):
    name = {"a": "semantic", "b": "bm25"}[team]
    print(f"{position:>2}  {name:<8}  {LABELS.get(judgments.get(product_id), 'unjudged'):<10}  {products.at[product_id, 'name'][:45]}")
# lib.experiments holds the same function, which the simulations use
print("same list from lib.experiments:", "yes" if experiments.team_draft(semantic, bm25, np.random.default_rng(7)) == (shown, teams) else "no")
