from collections import Counter

from lib.agreement import LABELS
from lib.recorded import rag_answers
from lib.store import load_products, load_queries, qrels

products, queries, judgments = load_products(), load_queries("test"), qrels("test")
answers = rag_answers().set_index(["query_id", "context"])

chandelier, claim = 58, "medium-sized"                     # one answer, read by hand
answer, judged = answers.loc[(chandelier, "semantic")], judgments[chandelier]
cited = answer["cited"][0]
print("query:", queries.at[chandelier, "query"])
print("answer:", answer["answer"])
print("cited product:", products.at[cited, "name"])
print(f"the cited product's text says {claim}:", "yes" if claim in products.at[cited, "description"] else "no")
print("the judges' label:", LABELS[judged[cited]])
print("exact products in this answer's context:", sum(judged.get(p, 0) == 2 for p in answer["context_ids"]))

retrieved = answers.drop("random", level="context")        # every citation from the two retrievers' contexts
labels = Counter(LABELS.get(judgments[query_id].get(p), "unjudged")
                 for (query_id, _), cited_ids in retrieved["cited"].items() for p in cited_ids)
print("cited products, semantic and bm25 contexts:", sum(labels.values()))
for label in ["exact", "partial", "irrelevant", "unjudged"]:
    print(f"cited products, {label}:", labels[label])
