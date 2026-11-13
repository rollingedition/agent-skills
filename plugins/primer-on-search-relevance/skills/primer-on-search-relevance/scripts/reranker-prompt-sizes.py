"""Counts the characters each reranker reads per test query at depth 20, from the products' text and the recorded prompts,
and the model calls each design makes. The prose's point rests on the characters and calls lines, and on the two designs
the store didn't record."""
import numpy as np

from lib.agreement import as_the_llm_saw
from lib.ranking import DEPTH, listwise_line
from lib.recorded import manifest
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text

products, queries = load_products(), load_queries("test")
semantic = SemanticSearch().run(queries, k=DEPTH)                # the 20 products each reranker reads
prompts, text = manifest("llm-rerank")["prompts"], product_text(products)

cross_encoder, pointwise, listwise = [], [], []                  # characters read per query
for query_id, query in queries["query"].items():
    shown = products.loc[semantic[query_id]]
    # one call per product, each reading the query and that product's text together
    cross_encoder.append(sum(len(query) + len(text[product_id]) for product_id in semantic[query_id]))
    # the pointwise prompt, filled in with the query and the product as the LLM saw it
    pointwise.append(sum(len(prompts["pointwise"].format(query=query, product=as_the_llm_saw(product)))
                         for _, product in shown.iterrows()))
    # products numbered from 1, as the listwise prompt shows them
    lines = "\n".join(f"[{number}] {listwise_line(product)}" for number, (_, product) in enumerate(shown.iterrows(), 1))
    listwise.append(len(prompts["listwise"].format(query=query, products=lines, n=DEPTH)))

# the cross-encoder and the pointwise LLM make one call per product; the listwise LLM makes one call per query
for name, calls, characters in [("cross-encoder", DEPTH, cross_encoder), ("llm pointwise", DEPTH, pointwise),
                                ("llm listwise", 1, listwise)]:
    print(f"{name}, model calls per query: {calls}")
    print(f"{name}, characters read per query, mean: {np.mean(characters):,.0f}")
print(f"llm pairwise, every pair in both orders, calls per query: {DEPTH * (DEPTH - 1)}")
# a sliding window of 20 products, moved 10 at a time: its starts are list positions 0, 10, ..., 80
window, step, depth = 20, 10, 100                                # a sliding window over a deeper list
print(f"llm listwise over the top {depth}, window {window}, step {step}, calls per query: {(depth - window) // step + 1}")
