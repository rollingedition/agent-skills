"""Applies SmolLM2's learned merges by hand, earliest first, to the pieces its pre-tokenizer makes of three product names.
The example asserts that the tokens match the library's, which the prose cites."""
import json

from tokenizers import Tokenizer

smollm2 = Tokenizer.from_file("data/smollm2-tokenizer/tokenizer.json")   # the book's pinned copy, read from examples/
spec = json.load(open("data/smollm2-tokenizer/tokenizer.json", encoding="utf-8"))
rank = {tuple(m.split(" ")): i for i, m in enumerate(spec["model"]["merges"])}   # lower rank: learned earlier; the file stores each merge as "a b"


def merge(piece):                                    # apply the learned merges, earliest first, until none applies
    syms = list(piece)
    while len(syms) > 1:
        pairs = [(rank.get(p, len(rank)), i) for i, p in enumerate(zip(syms, syms[1:]))]   # a pair with no merge ranks after all of them
        best, i = min(pairs)                         # the earliest-learned pair; on a tie, the leftmost
        if best == len(rank):
            break
        syms[i:i + 2] = [syms[i] + syms[i + 1]]      # the symbols at i and i + 1, joined into one
    return syms


for name in ["set of 2 barstools", "sled coffee table", "6.5 qt . slow cooker"]:
    # pre_tokenize_str returns (piece, offsets) pairs; only the pieces are merged
    pieces = [p for p, _ in smollm2.pre_tokenizer.pre_tokenize_str(name)]       # split into words, digits and bytes
    by_hand = [token for piece in pieces for token in merge(piece)]
    print(name, "->", " ".join(by_hand))
    assert by_hand == smollm2.encode(name).tokens    # the library's tokens for the same name
steps = [step["type"] for step in spec["pre_tokenizer"]["pretokenizers"]]
assert spec["pre_tokenizer"]["pretokenizers"][0]["individual_digits"]   # the Digits step comes first, and splits digits one at a time
print("pre-tokenizer steps:", ", ".join(steps))
