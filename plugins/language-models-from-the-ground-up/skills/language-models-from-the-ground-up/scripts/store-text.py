"""Counts the store's products in each split and the words in its training names, then prints one ordinary training name
for each of four kinds of product. The line "different words in training names" is the one the prose's point rests on,
since the rare product-line names are among the words it counts."""
from lib.store import load_products, ordinary_words, words

products = load_products()                            # no split given: every product, in all three splits
print("products:", f"{len(products):,}")
for split in ["train", "validation", "test"]:
    print(f"{split} products:", f"{(products['split'] == split).sum():,}")

train = products[products["split"] == "train"]        # only the training names count toward the word totals
print("words in training names:", f"{sum(len(words(name)) for name in train['name']):,}")
print("different words in training names:", f"{len({w for name in train['name'] for w in words(name)}):,}")
print()
common = ordinary_words(300)                          # words in 300 descriptions or more: a stricter bar than the book's 30
for kind in ["coffee table", "bar stool", "area rug", "bathroom vanity"]:      # one name of each kind, as examples
    print(next(name for name in train["name"] if kind in name and all(w in common or not w.isalpha() for w in words(name))))   # the first name whose words are all common; numbers and punctuation pass
