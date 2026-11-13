"""Counts, for each probe pair, the products the two top 10s share and the top-10 products of the right size, without scoring anything. The prose's point rests on the right-size lines for the hood, slow-cooker and bed probes, and on the seat-count and loveseat lines for the sofa probe."""
from lib.recorded import probes
from lib.semantic import SemanticSearch
from lib.store import load_products

# Probe queries written for the book, embedded by the same model. They have no judgments,
# so this example counts what each top 10 holds; it doesn't score anything.
probe_queries, probe_vectors = probes()
products = load_products()
names = products["name"]
width = products["attributes"].str.extract(r"\bwidth: ([\d.]+)", expand=False).astype(float)
semantic = SemanticSearch()


def states(size, unit):
    """Names that state this size, such as "7 qt" or "7-quart", but not "3.7 qt"."""
    return names.str.contains(rf"(?<![\d.]){size}[ -]?(?:{unit})")


RIGHT_SIZE = {                       # the size each probe asks for: the width attribute, or the name
    # within half an inch of 36 or 48, so a 35.75-inch hood counts as 36
    "36 inch kitchen hood": (width - 36).abs() <= 0.5, "48 inch kitchen hood": (width - 48).abs() <= 0.5,
    "4 qt slow cooker": states(4, "qt|quart"), "7 qt slow cooker": states(7, "qt|quart"),
    # the whole word, which also matches 'twin over full' bunk beds
    "twin bed": names.str.contains(r"\btwin\b"), "king bed": names.str.contains(r"\bking\b"),
    "2 seat sofa": names.str.contains(r"\bloveseat\b"),        # a two-seat sofa is a loveseat
}
DIGIT_ONLY = {"2 seat sofa": states(2, " in 1| piece"), "4 seat sofa": states(4, " in 1| piece")}

for pair in ["hood", "cooker", "bed", "seats"]:
    first, second = probe_queries.index[probe_queries["pair"] == pair]  # each pair is two probes, in file order
    tops = {row: semantic.search_vector(probe_vectors[row], k=10).index for row in (first, second)}
    print(f"{pair}, similarity of the two queries: {probe_vectors[first] @ probe_vectors[second]:.3f}")
    print(f"{pair}, products in both top 10s:", len(set(tops[first]) & set(tops[second])))
    for row, top in tops.items():
        query = probe_queries.at[row, "query"]
        if query in RIGHT_SIZE:
            print(f"{query}, right size in the top 10:", RIGHT_SIZE[query][top].sum())
        if query in DIGIT_ONLY:
            print(f"{query}, same digit but a piece count or 2 in 1:", DIGIT_ONLY[query][top].sum())
    print()
# the two counts the sofa probes ask for
print("catalog names that give a seat count:", (states(2, "seat") | states(4, "seat")).sum())
print("catalog products named loveseat:", names.str.contains(r"\bloveseat\b").sum())
