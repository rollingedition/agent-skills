"""Works out the probability of stool after a name that starts patio bar, order by order, with the chapter's formula.
It checks the result against lib.ngrams and against the module's probabilities summed over the vocabulary: the
by hand line should match the lib.ngrams line, and the summed line should be a probability distribution's total."""
from lib import bpe
from lib.names import name_tokens
from lib.ngrams import START, KneserNey

model = KneserNey(name_tokens("train"), 4)     # a 4-gram model; below the top order its counts are continuation counts, except for n-grams that start a name
context = tuple([START] + bpe.store_tokenizer().encode("patio bar"))     # a name that starts "patio bar"
token, d = "stool</w>", model.d                # </w> ends a word; d is the discount, 0.75 by default


def by_hand(context, k):                         # the chapter's formula, one order at a time
    if k == 0:
        return 1 / (len(model.vocabulary) + 1)   # order 0 is uniform over the vocabulary, with one more slot for an unseen token
    context = context[len(context) - (k - 1):] if k > 1 else ()     # the last k-1 tokens: the order-k model's own context
    following, total = model.counts[k][context], model.totals[k].get(context, 0)
    if total == 0:
        return by_hand(context, k - 1)           # a context never seen gives all its weight to the order below
    kept = max(following[token] - d, 0) / total                  # the discounted count
    passed_down = d * len(following) / total                     # what the discount frees for the order below
    print(f"order {k}: kept {kept:.4f}, passed down {passed_down:.4f}")
    return kept + passed_down * by_hand(context, k - 1)


print("by hand:", f"{by_hand(context, 4):.4f}")
print("lib.ngrams:", f"{model.probability(context, token):.4f}")
total = sum(model.probability(context, t) for t in model.vocabulary)
print("probabilities after the context, summed:", f"{total:.4f}")
