"""Builds one Kneser-Ney model per order from 1 to 5, scores each on the training names and on the validation names, and
draws both against the order. The gap between the two lines is what the prose reads: how far the model does better on text
it counted than on text it has not seen."""
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.names import name_tokens
from lib.ngrams import KneserNey, perplexity

from matplotlib.ticker import NullFormatter

train, validation = name_tokens("train"), name_tokens("validation")
orders = [1, 2, 3, 4, 5]
train_perplexity, validation_perplexity = [], []
for n in orders:
    # the same model is scored on both sets, so the two lines differ only in the text, and the gap between them is the model's
    model = KneserNey(train, n)
    train_perplexity.append(perplexity(model, train))
    validation_perplexity.append(perplexity(model, validation))
    print(f"Kneser-Ney {n}-gram training perplexity: {train_perplexity[-1]:.1f}")
    print(f"Kneser-Ney {n}-gram validation perplexity: {validation_perplexity[-1]:.1f}")

best = orders[validation_perplexity.index(min(validation_perplexity))]
print(f"lowest validation perplexity order: {best}")
gap = [v - t for v, t in zip(validation_perplexity, train_perplexity)]
# lists start at order 1, so the entry for order n is at index n - 1
print(f"gap at the {best}-gram: {gap[best - 1]:.1f}")
print(f"gap at the 5-gram: {gap[4]:.1f}")
# the training line falls at every order, because a longer context always fits the text it was counted from
assert all(a > b for a, b in zip(train_perplexity, train_perplexity[1:]))
print("training perplexity falls at every order: yes")
# on new text the validation line stops improving at its lowest order, and the gap is wider at the 5-gram
# the same offset: validation_perplexity[best - 1] is the lowest order's score
assert best == 4 and validation_perplexity[4] >= validation_perplexity[best - 1]
print("validation perplexity does not improve after the 4-gram: yes")
# gap[4] is the 5-gram, gap[best - 1] the lowest order's gap
assert gap[4] > gap[best - 1]
print("gap widens from the 4-gram to the 5-gram: yes")

fig, ax = new_figure()
ax.plot(orders, validation_perplexity, color=ACCENT, marker="o", markersize=3,
        label="Kneser-Ney model, validation names")
ax.plot(orders, train_perplexity, color=INK, linestyle="--", marker="o", markersize=3,
        label="Kneser-Ney model, training names")
ax.fill_between(orders, train_perplexity, validation_perplexity, color=MUTED, alpha=0.15, linewidth=0,
                label="gap between the two")
ax.set_yscale("log")
ax.yaxis.set_minor_formatter(NullFormatter())       # log ticks only at the labelled values, so the axis stays readable
ax.set_yticks([3, 10, 30, 100, 300, 1000])
ax.set_yticklabels(["3", "10", "30", "100", "300", "1000"])
ax.set_xticks(orders)
ax.set_xlabel("order of the model, n (n - 1 tokens of context)")
ax.set_ylabel("perplexity per token, log scale")
ax.legend(frameon=False, loc="upper right")
save(fig, "perplexity-by-order")
