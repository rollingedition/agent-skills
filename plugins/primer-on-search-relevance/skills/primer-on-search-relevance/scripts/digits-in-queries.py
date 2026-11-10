import pandas as pd

from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_products, load_queries, product_text, qrels

products, queries = load_products(), load_queries()
with_digit = queries[queries["query"].str.contains(r"\d")]       # both splits: a diagnosis, nothing is tuned
judgments = {query_id: grades for query_id, grades in qrels().items() if query_id in with_digit.index}
scores = pd.DataFrame({
    "split": with_digit["split"],
    "bm25": evaluate(LexicalSearch(products).run(with_digit, k=100), judgments)["ndcg@10"],
    "semantic": evaluate(SemanticSearch().run(with_digit, k=100), judgments)["ndcg@10"],
    "query": with_digit["query"],
}).round(3)

print("queries with a digit:", len(scores))
print(scores.to_string())
print("semantic better:", (scores["semantic"] > scores["bm25"]).sum())
print("bm25 better:", (scores["bm25"] > scores["semantic"]).sum())
print("gaps under 0.03:", ((scores["semantic"] - scores["bm25"]).abs() < 0.03).sum())

text = product_text(products).str.lower()
print("products whose text has the word 7qt:", text.str.contains(r"\b7qt\b").sum())
print("products whose text has 7 qt:", text.str.contains(r"(?<![\d.])7 qt\b").sum())
