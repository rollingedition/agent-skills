from tokenizers import Tokenizer

from lib import bpe
from lib.store import load_products

smollm2 = Tokenizer.from_file("data/smollm2-tokenizer/tokenizer.json")
store = bpe.store_tokenizer()

print("SmolLM2 vocabulary:", f"{smollm2.get_vocab_size():,}")
for name in ["set of 2 barstools", "6.5 qt . slow cooker", "48 '' wide genuine leather wingback chair"]:
    print(name)
    print("  SmolLM2:", " ".join(smollm2.encode(name).tokens))
    print("  store:  ", " ".join(store.encode(name)))

names = load_products("validation")["name"]
print("tokens per validation name, SmolLM2:", round(sum(len(smollm2.encode(n).ids) for n in names) / len(names), 2))
print("tokens per validation name, store:", round(sum(len(store.encode(n)) for n in names) / len(names), 2))
print("tokens per validation name, words:", round(sum(len(n.split()) for n in names) / len(names), 2))
print("sled at the start of a text:", " ".join(smollm2.encode("sled coffee table").tokens))
print("sled after a space:", " ".join(smollm2.encode(" sled coffee table").tokens))
words_total = sum(len(n.split()) for n in names)
print("SmolLM2 tokens per word:", round(sum(len(smollm2.encode(n).ids) for n in names) / words_total, 2))
