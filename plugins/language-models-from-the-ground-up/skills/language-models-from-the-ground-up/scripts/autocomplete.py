from lib.bigrams import Bigrams
from lib.store import load_products

model = Bigrams(load_products("train")["name"])

for typed in ["coffee", "bar", "kitchen", "outdoor", "patio bar"]:
    last_word = typed.split()[-1]                    # a bigram model sees only the last word
    suggestions = model.next_words(last_word, k=3)
    print(f"{typed:<10} -> " + ", ".join(f"'{word}' {p:.2f}" for word, p in suggestions))

names = load_products("train")["name"]
print("training names containing 'outdoor door':", sum("outdoor door" in n for n in names))
print("of them, followed by 'mat':", sum("outdoor door mat" in n for n in names))
