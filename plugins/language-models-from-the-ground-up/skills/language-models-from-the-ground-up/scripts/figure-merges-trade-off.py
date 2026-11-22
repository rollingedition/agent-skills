"""Draw tokens per word and the share of rare token types for 16 merge counts, from none to 16,000, on one merge axis.
The printed lines are the values the prose quotes, and the asserts check the two shape claims it makes."""
from collections import Counter

from lib import bpe
from lib.figures import ACCENT, INK, new_figure, save
from lib.store import load_products, words

import numpy as np
from matplotlib.ticker import FuncFormatter, PercentFormatter

GRID = [0, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 14000, 16000]

training, validation = load_products("train"), load_products("validation")
counts = Counter(w for text in training["name"] + " " + training["description"] for w in words(text))
merges = bpe.train(counts, merges=max(GRID))         # the first k merges of one longer run are a k-merge tokenizer
validation_words = [w for text in validation["name"] + " " + validation["description"] for w in words(text)]

per_word, rare = [], []
for k in GRID:
    encode = bpe.Tokenizer(merges[:k], bpe.alphabet(counts)).encode_word if k else bpe.symbols   # no merges: characters
    seen = Counter(t for w, n in counts.items() for t in encode(w) for _ in range(n))   # each token counted as often as its word
    per_word.append(sum(len(encode(w)) for w in validation_words) / len(validation_words))
    rare.append(sum(1 for n in seen.values() if n < 20) / len(seen))   # rare: seen fewer than 20 times in the training text

low = int(np.argmin(rare))                           # argmin keeps the first, so ties go to fewer merges
slopes = np.diff(rare) / np.diff(GRID)               # slopes[i]: the rise per merge from setting i to setting i + 1
steepest = int(np.argmax(slopes))
assert (slopes[:low] <= 0).all() and (slopes[low:] >= 0).all()   # down to the low point, up after it
assert (per_word[0] - per_word[4]) / 2000 > (per_word[4] - per_word[-1]) / 14000   # per merge: [4] is 2,000, [-1] 16,000

print("settings drawn:", len(GRID))
print("merges with the fewest rare token types:", f"{GRID[low]:,}")
print("rare token types at 12,000 merges:", f"{rare[GRID.index(12000)]:.0%}")
print("steepest rise in rare token types starts at merges:", f"{GRID[steepest]:,}")
print("steepest rise in rare token types ends at merges:", f"{GRID[steepest + 1]:,}")   # the next setting on the grid
print("tokens per word falls faster before 2,000 merges than after: yes")
print("rare token types fall to a low, then climb, across the settings: yes")

fig, (top, bottom) = new_figure(rows=2, height=4.4)
top.plot(GRID, per_word, color=INK, marker="o", markersize=3, label="tokens per word")
bottom.plot(GRID, rare, color=ACCENT, marker="o", markersize=3, label="rare token types")
top.set(ylabel="tokens per word", ylim=(0, None))
bottom.set(ylabel="share of token types\nseen under 20 times", ylim=(0, None),   # the top limit fits the data
           xlabel="merges learned by the tokenizer", xticks=[0, 4000, 8000, 12000, 16000])
bottom.yaxis.set_major_formatter(PercentFormatter(1.0))
bottom.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
top.legend(loc="upper right")
bottom.legend(loc="upper center")
save(fig, "merges-trade-off")
