"""Draws BM25's term-frequency part for a product of average length, at k1 0.5, 1.5 and 2.0, for a term that occurs 0 to 10 times. The prose rests on the weights at 10 occurrences and on the value at a million, which show how each line levels off."""
from lib.figures import ACCENT, INK, MUTED, new_figure, save

B = 0.75                                   # bm25s's default b, which the store keeps
DEFAULT_K1 = 1.5                           # bm25s's default k1, which the store keeps
COUNTS = list(range(11))                   # how many times the term occurs in the product

fig, ax = new_figure(height=2.6)
for k1, color, style in ((0.5, INK, "-"), (DEFAULT_K1, ACCENT, "-"), (2.0, MUTED, "--")):
    label = f"k1 = {k1}" + (", the default" if k1 == DEFAULT_K1 else "")
    length = 1 - B + B * 1.0               # a product of average length: its length over the average is 1
    weight = lambda tf: tf / (tf + k1 * length)  # BM25's term-frequency part, as the chapter writes it
    print(f"term weight at 1 occurrence, k1 {k1}: {weight(1):.3f}")
    print(f"term weight at 10 occurrences, k1 {k1}: {weight(10):.3f}")
    print(f"term weight at 1000000 occurrences, k1 {k1}: {weight(1_000_000):.3f}")  # the ceiling, 1, is what it nears
    print(f"gap below 1 at 1000000 occurrences, k1 {k1}: {1 - weight(1_000_000):.1e}")  # how far the weight still is from the ceiling
    ax.plot(COUNTS, [weight(tf) for tf in COUNTS], color=color, linestyle=style, marker="o", markersize=3, label=label)
ax.set_xlabel("occurrences of the term in the product")
ax.set_ylabel("term-frequency weight")
ax.set_xlim(0, 10)
ax.set_ylim(0, 1.05)
ax.legend(loc="lower right", frameon=False)
save(fig, "bm25-term-saturation")
