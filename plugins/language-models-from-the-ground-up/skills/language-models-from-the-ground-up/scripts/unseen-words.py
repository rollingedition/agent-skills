from collections import Counter

from lib.store import is_ordinary, load_products, words

train_words = Counter(w for name in load_products("train")["name"] for w in words(name))
validation = [w for name in load_products("validation")["name"] for w in words(name)]
unseen = [w for w in validation if w not in train_words]

print("different words in training names:", f"{len(train_words):,}")
print("words seen once in training:", f"{sum(1 for n in train_words.values() if n == 1):,}")
print("validation words:", f"{len(validation):,}")
print("validation words never seen in training:", f"{len(unseen):,}")
print("share never seen in training:", f"{len(unseen) / len(validation):.1%}")
print("share of them that are rare words, most often product lines' names:",
      f"{sum(not is_ordinary(w) for w in unseen) / len(unseen):.0%}")
print("most frequent of the ordinary ones:", ", ".join(w for w, _ in Counter(w for w in unseen if is_ordinary(w)).most_common(6)))
