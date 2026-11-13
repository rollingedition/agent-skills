"""Asks the 4-gram model for its three likeliest next tokens after bar, patio bar and outdoor bar, each typed as the start
of a name, then counts the training names that contain outdoor bar. The three suggestion lines carry the point, and the last line
counts the training names with outdoor bar in them."""
from lib import bpe
from lib.names import name_tokens
from lib.ngrams import START, KneserNey

model = KneserNey(name_tokens("train"), 4)
tokenizer = bpe.store_tokenizer()
candidates = sorted(model.vocabulary)       # sorted first, so tokens with equal probability keep alphabetical order

for typed in ["bar", "patio bar", "outdoor bar"]:
    # padded with start markers, then the last three tokens: a short prefix still gives a full context
    context = tuple([START] * 3 + tokenizer.encode(typed))[-3:]
    ranked = sorted(candidates, key=lambda t: -model.probability(context, t))[:3]     # negated, so the likeliest sort first
    print(f"{typed:<12} -> " + ", ".join(f"{t.replace('</w>', '')} {model.probability(context, t):.2f}" for t in ranked))
# each name as one string of tokens, so the check below matches whole tokens rather than parts of them
names = [" ".join(t) for t in name_tokens("train")]
print("training names containing 'outdoor bar':", sum("outdoor</w> bar</w>" in n for n in names))
