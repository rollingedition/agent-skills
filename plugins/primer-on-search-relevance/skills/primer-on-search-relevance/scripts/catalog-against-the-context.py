from statistics import median

from lib.agreement import as_the_llm_saw
from lib.recorded import manifest, rag_answers
from lib.store import load_products

recording = manifest("rag-answers")
window = recording["options"]["num_ctx"]
print("model:", recording["model"])
print("licence in the manifest:", recording["model_licence"])
print("instructions:", recording["prompts"].split("\n")[0])
print("context window the recording set, in tokens:", window)

products = load_products()
words = {product_id: len(f"ID: {product_id}\n{as_the_llm_saw(product)}".split())    # each product as the LLM read it
         for product_id, product in products.iterrows()}
instructions = len(recording["prompts"].split())                  # the prompt's own words, without the query
prompts = [instructions + sum(words[p] for p in ids) for ids in rag_answers()["context_ids"]]
catalog = sum(words.values())
print(f"words in the catalog as the LLM reads it: {catalog:,}")
print(f"words in one prompt with five products, median: {median(prompts):,.0f}")
print(f"the catalog against one prompt: {catalog / median(prompts):,.0f} times")
print(f"the catalog against the recording's window, at one token per word: {catalog / window:,.0f} times")
print(f"the catalog against 200,000 tokens, at one token per word: {catalog / 200_000:.1f} times")
