import re

from lib.store import load_labels, load_products, load_queries, product_text


def words(text):
    """Lowercase word tokens: a rough stand-in for what lexical search matches."""
    return set(re.findall(r"\w+", text.lower()))


products, queries, labels = load_products(), load_queries(), load_labels()
text_words = {product_id: words(text) for product_id, text in product_text(products).items()}
attribute_words = {product_id: words(text) for product_id, text in products["attributes"].items()}
query_words = {query_id: words(query) for query_id, query in queries["query"].items()}
pairs = list(zip(labels["query_id"], labels["product_id"]))
labels["in text"] = [query_words[query_id] <= text_words[product_id] for query_id, product_id in pairs]
labels["in text or attributes"] = [query_words[query_id] <= text_words[product_id] | attribute_words[product_id]
                                   for query_id, product_id in pairs]

matched = labels[labels["in text"]]
print(f"exact share of all judged pairs: {(labels['label'] == 'exact').mean():.3f}")
print(f"judged pairs whose text has every query word: {len(matched):,}")
for label in ["exact", "partial", "irrelevant"]:
    print(f"of them {label}: {(matched['label'] == label).mean():.3f}")

exact = labels[labels["label"] == "exact"]
print(f"exact pairs: {len(exact):,}")
print(f"exact pairs whose text misses a query word: {(~exact['in text']).sum():,}")
print(f"of them, still missing one with attributes added: {(~exact['in text or attributes']).sum():,}")

curtains = list(exact.loc[exact["query_id"] == 246, "product_id"])                 # clear shower curtain
unsaid = [product_id for product_id in curtains if "clear" not in text_words[product_id]]
print("exact products for clear shower curtain:", len(curtains))
print("of them without the word clear in their text:", len(unsaid))
print("of those, with clear in their attributes:", sum("clear" in attribute_words[product_id] for product_id in unsaid))
