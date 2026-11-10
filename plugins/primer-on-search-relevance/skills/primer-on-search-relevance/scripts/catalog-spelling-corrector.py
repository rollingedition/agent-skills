import re
from collections import Counter

from lib.queries import correct_query
from lib.store import load_products, load_queries, product_text

texts = product_text(load_products()).str.lower()
counts = Counter(re.findall(r"[a-z]+", " ".join(texts)))       # the lexicon, and how common each word is


def edits1(word):
    """Every string one edit away: a deletion, a swap of two neighbouring letters, a replacement or an insertion."""
    splits = [(word[:cut], word[cut:]) for cut in range(len(word) + 1)]
    letters = "abcdefghijklmnopqrstuvwxyz"
    return ({left + right[1:] for left, right in splits if right}
            | {left + right[1] + right[0] + right[2:] for left, right in splits if len(right) > 1}
            | {left + letter + right[1:] for left, right in splits if right for letter in letters}
            | {left + letter + right for left, right in splits for letter in letters})


def correct(word):
    """Keep a word the catalog uses. Otherwise take the commonest catalog word one edit away, else two."""
    if not word.isalpha() or word in counts:
        return word
    candidates = {edit for edit in edits1(word) if edit in counts} or {
        two for edit in edits1(word) for two in edits1(edit) if two in counts}
    return max(sorted(candidates), key=counts.get) if candidates else word


queries = load_queries()
corrected = queries["query"].map(lambda query: " ".join(correct(word) for word in query.lower().split()))
changed = queries[corrected != queries["query"].str.lower()]
print(f"catalog words: {len(counts):,}")
print("queries changed:", len(changed))
print("of them, train queries:", (changed["split"] == "train").sum())
for query_id, query in changed["query"].items():
    print(f"  {query} ({changed.at[query_id, 'split']}), corrected: {corrected[query_id]}")
same = corrected.equals(queries["query"].map(lambda query: correct_query(query, counts)))
print("same as lib.queries.correct_query:", same)
for word in ["tye", "tie", "the", "kohler", "whitehaven", "malachi", "luau"]:      # P(c), as counts
    print(f"catalog count of {word}:", counts[word])
