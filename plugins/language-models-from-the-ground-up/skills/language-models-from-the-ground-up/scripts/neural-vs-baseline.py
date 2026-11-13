"""The window model and the 4-gram baseline, each scored by perplexity per token on the same validation names. The
prose's point rests on the two printed perplexities."""
from lib import neural
from lib.names import name_tokens
from lib.ngrams import KneserNey, perplexity

train, validation = name_tokens("train"), name_tokens("validation")     # both models are scored on the same tokens of the same names
print("window model validation perplexity:", f"{neural.perplexity(validation):.1f}")      # the window model, from its saved weights
print("4-gram baseline validation perplexity:", f"{perplexity(KneserNey(train, 4), validation):.1f}")   # a 4-gram: each token is predicted from the three before it
