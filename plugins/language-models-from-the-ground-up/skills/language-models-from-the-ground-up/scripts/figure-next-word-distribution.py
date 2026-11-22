"""Draws how much of the probability after coffee and after the start marker the likeliest words hold, one more word at a time.
The printed shares show the shape: after coffee one word holds most of it, after the start marker fifteen words hold little."""
from lib.bigrams import END, START, Bigrams
from lib.figures import ACCENT, INK, new_figure, save
from lib.store import is_ordinary, load_products

model = Bigrams(load_products("train")["name"])          # the same counts next-word-probabilities uses, training split only
contexts = [("coffee", "coffee", ACCENT), (START, "start marker", INK)]   # START is <s>, the marker before every name


def shown(word: str) -> str:
    """The word as the figure prints it; a product line's name is hidden, as everywhere in this book."""
    if word == END:
        return "end marker"
    return word if is_ordinary(word) else "[name]"


fig, ax = new_figure(height=3.8)                         # one axis from 0 to 1 for both contexts, so their lines compare directly
for word, name, color in contexts:
    # Sort by count, then by word, so ties come out in the same order on every run.
    ranked = sorted(model.counts[word].items(), key=lambda item: (-item[1], item[0]))[:15]
    total = model.totals[word]                           # every word that followed this context, not only the 15 drawn
    # The share held by the 1, 2, ... 15 likeliest words: the line the figure draws, ending at the share of the 15.
    cumulative = [sum(n for _, n in ranked[:k]) / total for k in range(1, len(ranked) + 1)]
    ax.plot(range(1, len(cumulative) + 1), cumulative, color=color, marker="o", markersize=3, label=f"after {name}")
    print(f"likeliest word after {name}: {shown(ranked[0][0])}")
    print(f"top probability after {name}: {cumulative[0]:.3f}")
    print(f"words that followed {name}: {len(model.counts[word])}")
    print(f"share of probability in the 15 drawn, after {name}: {cumulative[-1]:.3f}")

ax.set_xticks(range(1, 16))
ax.set_ylim(0, 1)
ax.set_xlabel("number of likeliest words counted, most likely first")
ax.set_ylabel("share of the probability they hold")
ax.legend(loc="center right")
save(fig, "next-word-distribution")
