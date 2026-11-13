from lib.store import load_products, ordinary_words, words

products = load_products()
print("products:", f"{len(products):,}")
for split in ["train", "validation", "test"]:
    print(f"{split} products:", f"{(products['split'] == split).sum():,}")

train = products[products["split"] == "train"]
print("words in training names:", f"{sum(len(words(name)) for name in train['name']):,}")
print("different words in training names:", f"{len({w for name in train['name'] for w in words(name)}):,}")
print()
common = ordinary_words(300)                          # words in 300 descriptions or more: plainly not names
for kind in ["coffee table", "bar stool", "area rug", "bathroom vanity"]:      # one name of each kind, as examples
    print(next(name for name in train["name"] if kind in name and all(w in common or not w.isalpha() for w in words(name))))
