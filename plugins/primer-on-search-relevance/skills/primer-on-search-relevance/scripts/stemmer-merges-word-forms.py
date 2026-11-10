import Stemmer

from lib.lexical_by_hand import InvertedIndex
from lib.store import load_products, product_text


def strip_suffix(word):
    """A stemmer by hand: cut the first ending that matches, if at least three letters are left."""
    for ending in ["ing", "es", "ed", "s"]:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[: -len(ending)]
    return word


stemmer = Stemmer.Stemmer("english")          # Snowball English, also called Porter2
words = ["floats", "floating", "molding", "molded", "moldings", "shelves", "shelving", "shelf"]
for word, stem in zip(words, stemmer.stemWords(words)):
    print(f"{word}: snowball {stem}, by hand {strip_suffix(word)}")

products = load_products()
text = product_text(products)
plain, stemmed = InvertedIndex(text), InvertedIndex(text, stem=True)
print()
for word in ["floats", "molding"]:
    print(f"products with {word}:", len(plain.postings[word]))
    print(f"products with the stem of {word}:", len(stemmed.postings[stemmer.stemWord(word)]))
float_products = list(stemmed.postings["float"])
print("products with the stem of floats that say floating:", len(plain.postings["floating"].keys() & set(float_products)))
for product_class, count in products.loc[float_products, "product_class"].value_counts().head(2).items():
    print(f"products with the stem of floats in {product_class}: {count}")
print(f"vocabulary without stemming: {len(plain.postings):,} terms")
print(f"vocabulary with stemming: {len(stemmed.postings):,} terms")
print(f"vocabulary reduction: {1 - len(stemmed.postings) / len(plain.postings):.0%}")
