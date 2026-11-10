from collections import Counter

import bm25s

from lib.store import load_products, load_queries, product_text, qrels

products, queries, judgments = load_products(), load_queries("train"), qrels("train")


def words(texts):
    """The tokens BM25 matches on: bm25s's default tokenizer with English stopwords, as in lib.lexical."""
    tokenized = bm25s.tokenize(texts, stopwords="en", return_ids=False, show_progress=False)
    return [set(tokens) for tokens in tokenized]


product_words = dict(zip(products.index, words(product_text(products).tolist())))
query_words = dict(zip(queries.index, words(queries["query"].tolist())))
exact_pairs = [(query_id, product_id) for query_id in queries.index
               for product_id, grade in judgments[query_id].items() if grade == 2]
missed = Counter(word for query_id, product_id in exact_pairs
                 for word in query_words[query_id] - product_words[product_id])
missing = sum(not query_words[query_id] <= product_words[product_id] for query_id, product_id in exact_pairs)
print("exact train pairs:", len(exact_pairs))
print("exact pairs missing a query word:", missing)
print(f"share missing a query word: {missing / len(exact_pairs):.3f}")
print("most often missing:", ", ".join(f"{word} ({count})" for word, count in missed.most_common(8)))

exact = [product_id for query_id, product_id in exact_pairs if query_id == 453]   # midcentury tv unit
print("exact products for midcentury tv unit:", len(exact))
for word in ["midcentury", "unit", "stand"]:
    print(f"exact products containing {word}:", sum(word in product_words[product_id] for product_id in exact))
mid_century = product_text(products)[exact].str.contains("mid-century")
print("exact products whose text says mid-century:", mid_century.sum())
