from lib.lexical_by_hand import InvertedIndex, tokenize
from lib.store import load_products, product_text

products = load_products()
positions = {}            # {term: {product_id: [where the term occurs in the name, counted after stop words go]}}
for product_id, name in products["name"].items():
    for place, term in enumerate(tokenize(name, stem=True)):
        positions.setdefault(term, {}).setdefault(product_id, []).append(place)


def has_phrase(product_id, terms):
    """True if the terms occur next to each other, in this order, in the product's name."""
    def places(term):
        return positions.get(term, {}).get(product_id, [])
    return any(all(start + offset in places(term) for offset, term in enumerate(terms)) for start in places(terms[0]))


index = InvertedIndex(product_text(products), stem=True)
print("same bm25 scores for barn door and door barn:", index.bm25("barn door") == index.bm25("door barn"))
both = set(positions["barn"]) & set(positions["door"])
print("names with barn and door:", len(both))
print("names with the phrase barn door:", sum(has_phrase(product_id, ["barn", "door"]) for product_id in both))
for product_id in sorted(product_id for product_id in both if not has_phrase(product_id, ["barn", "door"])):
    print("  ", products.at[product_id, "name"])
