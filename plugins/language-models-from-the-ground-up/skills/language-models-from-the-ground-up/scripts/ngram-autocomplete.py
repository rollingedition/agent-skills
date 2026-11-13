from lib import bpe
from lib.names import name_tokens
from lib.ngrams import START, KneserNey

model = KneserNey(name_tokens("train"), 4)
tokenizer = bpe.store_tokenizer()
candidates = sorted(model.vocabulary)

for typed in ["bar", "patio bar", "outdoor bar"]:
    context = tuple([START] * 3 + tokenizer.encode(typed))[-3:]          # the last three tokens typed
    ranked = sorted(candidates, key=lambda t: -model.probability(context, t))[:3]
    print(f"{typed:<12} -> " + ", ".join(f"{t.replace('</w>', '')} {model.probability(context, t):.2f}" for t in ranked))
names = [" ".join(t) for t in name_tokens("train")]
print("training names containing 'outdoor bar':", sum("outdoor</w> bar</w>" in n for n in names))
