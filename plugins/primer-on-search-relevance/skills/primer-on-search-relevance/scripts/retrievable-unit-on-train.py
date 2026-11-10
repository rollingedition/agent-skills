import numpy as np

from lib.generation import UnitSearch, sentences
from lib.metrics import judged_at_k, precision_at_k, recall_at_k
from lib.store import load_products, load_queries, product_text, qrels

products = load_products()
lengths = products["description"].str.split().str.len()
print(f"products with no description: {(lengths == 0).sum():,}")
print(f"descriptions the sample cut short: {products['description'].str.endswith(' ...').sum():,}")
print(f"description words, median of the others: {lengths[lengths > 0].median():.0f}")
print(f"product text words per product, most: {product_text(products).str.split().str.len().max()}")

header = products["name"] + ". " + products["product_class"] + ". " + products["category"] + ". "   # the other fields
pieces = [(p, piece) for p, text in products["description"].items() for piece in sentences(text) or [""]]
print(f"description sentences: {sum(piece != '' for _, piece in pieces):,}")
print("last sentence of product 8171:", sentences(products.at[8171, "description"])[-1])
units = {                                              # unit name: (texts to index, the product each belongs to)
    "whole product": (product_text(products), products.index),
    "name only": (products["name"], products.index),
    "description only": (products["description"], products.index),
    "sentences": ([piece for _, piece in pieces], [p for p, _ in pieces]),
    "sentences with the other fields": ([header[p] + piece for p, piece in pieces], [p for p, _ in pieces]),
}
train, judgments = load_queries("train"), qrels("train")      # choosing a unit is tuning: train queries only
scores = {}
for name, (texts, owners) in units.items():
    run = UnitSearch(list(texts), list(owners)).run(train, k=5)                    # equal scores by product_id
    for metric in [precision_at_k, recall_at_k, judged_at_k]:
        scores[name, metric] = np.mean([metric(run[q], judgments[q], 5) for q in train.index])
        print(f"{name}, train {metric.__name__.replace('_at_k', '')}@5: {scores[name, metric]:.3f}")
    flipped = UnitSearch(list(texts), [-p for p in owners]).run(train, k=5)        # negated owners: ties go to the highest ID
    changed = sum(set(run[q]) != {-p for p in flipped[q]} for q in train.index)
    print(f"{name}, train queries whose top 5 changes with ties reversed: {changed}")
print("highest train precision@5:", max(units, key=lambda name: scores[name, precision_at_k]))
for metric in [precision_at_k, recall_at_k]:
    gap = scores["whole product", metric] - scores["sentences with the other fields", metric]
    print(f"whole product minus sentences with the other fields, train {metric.__name__.replace('_at_k', '')}@5: {gap:.3f}")
