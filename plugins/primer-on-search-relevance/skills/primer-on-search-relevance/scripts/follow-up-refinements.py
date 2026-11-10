import numpy as np

from lib.queries import mentions
from lib.recorded import llm_conversations
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

products, judgments, semantic = load_products(), qrels("test"), SemanticSearch()
attributes, text = products["attributes"], product_text(products)        # the embeddings read only the text
conversations, vectors = llm_conversations()                 # follow-ups we wrote for the book, not shoppers'
print("conversations:", len(conversations))
example = conversations.iloc[4]
print(f"first query: {load_queries().at[example['query_id'], 'query']}")
print(f"follow-up: {example['follow_up']}")
print(f"standalone: {example['standalone']}")

shares, filtered_lengths = {}, []                            # shares: (top 10, measure) -> one share per conversation
for row, (first, value) in enumerate(zip(conversations["query_id"], conversations["value"])):
    standalone = semantic.search_vector(vectors["standalone"][row], k=100).index
    stated = mentions(standalone, value, attributes) | mentions(standalone, value, text)
    tops = {"first query": semantic.search(first, k=10).index,
            "follow-up alone": semantic.search_vector(vectors["follow_up"][row], k=10).index,
            "turns joined": semantic.search_vector(vectors["joined"][row], k=10).index,
            "standalone": standalone[:10],
            "standalone, filtered": standalone[stated][:10]}         # given the value, which a live system extracts
    filtered_lengths.append(len(tops["standalone, filtered"]))
    for name, top in tops.items():
        in_attributes = mentions(top, value, attributes)
        in_either = in_attributes | mentions(top, value, text)
        right_kind = np.array([judgments[first].get(product_id, 0) >= 1 for product_id in top], dtype=bool)
        for measure, hits in [("refinement in attributes", in_attributes), ("refinement in text or attributes", in_either),
                              ("right kind", right_kind), ("right kind with the refinement", in_either & right_kind)]:
            shares.setdefault((name, measure), []).append(hits.sum() / 10)     # empty places count as misses
for (name, measure), values in shares.items():
    print(f"{name}, {measure}: {np.mean(values):.3f}")

kept = np.subtract(shares["standalone", "refinement in text or attributes"], shares["turns joined", "refinement in text or attributes"])
print(f"standalone against turns joined, more, fewer, same: {(kept > 0).sum()}, {(kept < 0).sum()}, {(kept == 0).sum()}")
print("conversations the filter leaves with fewer than 10 products:", sum(length < 10 for length in filtered_lengths))
