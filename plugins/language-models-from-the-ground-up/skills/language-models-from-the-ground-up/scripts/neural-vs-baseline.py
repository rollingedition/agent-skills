from lib import neural
from lib.names import name_tokens
from lib.ngrams import KneserNey, perplexity

train, validation = name_tokens("train"), name_tokens("validation")
print("window model validation perplexity:", f"{neural.perplexity(validation):.1f}")
print("4-gram baseline validation perplexity:", f"{perplexity(KneserNey(train, 4), validation):.1f}")
