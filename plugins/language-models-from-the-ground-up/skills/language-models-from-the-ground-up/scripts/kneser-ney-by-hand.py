from lib import bpe
from lib.names import name_tokens
from lib.ngrams import START, KneserNey

model = KneserNey(name_tokens("train"), 4)
context = tuple([START] + bpe.store_tokenizer().encode("patio bar"))     # a name that starts "patio bar"
token, d = "stool</w>", model.d


def by_hand(context, k):                         # the chapter's formula, one order at a time
    if k == 0:
        return 1 / (len(model.vocabulary) + 1)
    context = context[len(context) - (k - 1):] if k > 1 else ()
    following, total = model.counts[k][context], model.totals[k].get(context, 0)
    if total == 0:
        return by_hand(context, k - 1)
    kept = max(following[token] - d, 0) / total                  # the discounted count
    passed_down = d * len(following) / total                     # what the discount frees for the order below
    print(f"order {k}: kept {kept:.4f}, passed down {passed_down:.4f}")
    return kept + passed_down * by_hand(context, k - 1)


print("by hand:", f"{by_hand(context, 4):.4f}")
print("lib.ngrams:", f"{model.probability(context, token):.4f}")
total = sum(model.probability(context, t) for t in model.vocabulary)
print("probabilities after the context, summed:", f"{total:.4f}")
