"""Scores three rankings of one query's judged products under three labelings, to show what each labeling counts as
relevant. The prose's point rests on the `grades` lines, since only the grades separate the three rankings."""
from lib.metrics import ndcg_at_k
from lib.store import load_products, qrels

classes = load_products()["product_class"]
judgments = qrels()[246]                                     # clear shower curtain: {product_id: grade}


def first_ten(grade, product_class=None):
    """Ten products judged with this grade for the query, in product_id order."""
    # sorted(judgments) takes product_id order as the tie-break; None for product_class means any class
    return [product_id for product_id in sorted(judgments) if judgments[product_id] == grade
            and product_class in (None, classes[product_id])][:10]


rankings = {"clear curtains": first_ten(2),                                   # exact
            "other curtains": first_ten(1, "Shower Curtains"),               # partial: not clear
            "hooks": first_ten(0, "Shower Curtain Hooks and Accessories")}   # irrelevant
labelings = {"exact only": {2: 1, 1: 0, 0: 0},              # binary: relevant means exact
             "exact or partial": {2: 1, 1: 1, 0: 0},        # binary: relevant means exact or partial
             "grades": {2: 2, 1: 1, 0: 0}}                  # graded: the book's grades as gains

print("exact products for this query:", sum(grade == 2 for grade in judgments.values()))
# the ideal top 10 holds the ten highest grades, so counting the 2s counts the exact products in it
print("exact products in the ideal top 10:", sorted(judgments.values(), reverse=True)[:10].count(2))
for labeling, gain in labelings.items():
    gains = {product_id: gain[grade] for product_id, grade in judgments.items()}
    for name, ranking in rankings.items():
        print(f"{name}, {labeling}: {ndcg_at_k(ranking, gains, 10):.3f}")
