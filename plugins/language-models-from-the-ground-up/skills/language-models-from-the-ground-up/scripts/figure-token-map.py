"""Draws the SVD vectors of tokens from four kinds of word on the two directions along which they spread most. It prints
how much of that spread the picture keeps, the cosine similarity within and between the kinds, and each kind's centre on
the first direction: the prose reads those, never distances off the picture."""
from lib.vectors import svd_vectors                              # the same 64-number vectors svd-neighbours.py uses

import numpy as np

from lib.figures import ACCENT, INK, MUTED, new_figure, save

# picked by hand: each group starts from one of the six tokens svd-neighbours lists; the rest are words of its kind,
# some of them that list's neighbours and some not. The seating group is the one the prose names first, so ACCENT.
groups = {                                                       # name: (tokens, marker and colour, as the legend shows them)
    "materials": (["oak", "walnut", "pine", "teak", "espresso"], dict(color=MUTED, marker="o")),
    "seating": (["sofa", "sectional", "loveseat", "chaise", "recliner"], dict(color=ACCENT, marker="s")),
    "outdoor": (["patio", "porch", "outdoor", "bistro", "umbrella"], dict(color=INK, marker="^")),
    "colours": (["blue", "green", "beige", "white", "black"], dict(edgecolors=INK, facecolors="none", marker="D")),
}
vectors, vocabulary = svd_vectors()
words = [w for tokens, _ in groups.values() for w in tokens]
labels = np.array([name for name, (tokens, _) in groups.items() for _ in tokens])
# the vocabulary marks each word's last token with "</w>", so a word's vector is found by adding that suffix
chosen = vectors[[list(vocabulary).index(w + "</w>") for w in words]]  # unit-length rows, so chosen @ chosen.T is the cosine matrix

# the two principal directions of the chosen vectors; each sign is fixed so every machine draws the same picture
_, singular, directions = np.linalg.svd(chosen - chosen.mean(axis=0), full_matrices=False)
directions[:2] *= np.sign(directions[:2].sum(axis=1, keepdims=True))
points = (chosen - chosen.mean(axis=0)) @ directions[:2].T
print(f"variance held by the two drawn directions: {(singular[:2] ** 2).sum() / (singular ** 2).sum():.2f}")
print(f"variance left out of the picture: {(singular[2:] ** 2).sum() / (singular ** 2).sum():.2f}")

pairs = np.triu_indices(len(words), k=1)                        # each pair once, never a token with itself
same = (labels[:, None] == labels[None, :])[pairs]
sims = (chosen @ chosen.T)[pairs]
print(f"mean cosine within a group: {sims[same].mean():.2f}")
print(f"mean cosine between groups: {sims[~same].mean():.2f}")
assert sims[same].mean() > sims[~same].mean()
print("within a group more similar than between: yes")
centre = {name: points[labels == name, 0].mean() for name in groups}
for name in groups:
    print(f"centre of {name}, first direction: {centre[name]:.2f}")
assert max(centre["seating"], centre["outdoor"]) < min(centre["materials"], centre["colours"])
print("seating and outdoor centres on one side of materials and colours: yes")

fig, ax = new_figure(height=3.6)
for name, (tokens, style) in groups.items():
    ax.scatter(points[labels == name, 0], points[labels == name, 1], s=28, label=name, **style)
nudge = {"sofa": (-30, -10), "sectional": (2, -11), "porch": (-6, 6), "outdoor": (6, -10)}   # keep close labels apart
for word, (x, y) in zip(words, points):
    ax.annotate(word, (x, y), xytext=nudge.get(word, (4, 3)), textcoords="offset points", fontsize=8, color=INK)
ax.set_xlabel("first principal direction (arbitrary units)")
ax.set_ylabel("second principal direction (arbitrary units)")
ax.legend(loc="best", fontsize=8)
save(fig, "token-map")
