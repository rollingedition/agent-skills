import json

from tokenizers import Tokenizer

smollm2 = Tokenizer.from_file("data/smollm2-tokenizer/tokenizer.json")
spec = json.load(open("data/smollm2-tokenizer/tokenizer.json", encoding="utf-8"))
rank = {tuple(m.split(" ")): i for i, m in enumerate(spec["model"]["merges"])}   # lower rank: learned earlier


def merge(piece):                                    # apply the learned merges, earliest first, until none applies
    syms = list(piece)
    while len(syms) > 1:
        pairs = [(rank.get(p, len(rank)), i) for i, p in enumerate(zip(syms, syms[1:]))]
        best, i = min(pairs)
        if best == len(rank):
            break
        syms[i:i + 2] = [syms[i] + syms[i + 1]]
    return syms


for name in ["set of 2 barstools", "sled coffee table", "6.5 qt . slow cooker"]:
    pieces = [p for p, _ in smollm2.pre_tokenizer.pre_tokenize_str(name)]       # split into words, digits and bytes
    by_hand = [token for piece in pieces for token in merge(piece)]
    print(name, "->", " ".join(by_hand), "| same as the library:", by_hand == smollm2.encode(name).tokens)
steps = [step["type"] for step in spec["pre_tokenizer"]["pretokenizers"]]
print("pre-tokenizer steps:", ", ".join(steps), "| digits one at a time:", spec["pre_tokenizer"]["pretokenizers"][0]["individual_digits"])
