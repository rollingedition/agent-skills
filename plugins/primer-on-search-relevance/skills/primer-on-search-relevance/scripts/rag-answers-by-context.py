from lib.generation import PLANNED_TEST_COMPARISONS, THRESHOLD, report_planned, score_answers
from lib.lexical import LexicalSearch
from lib.recorded import rag_answers
from lib.store import load_products, load_queries, qrels

answers = rag_answers()
stored = answers[answers["context"] == "bm25"].set_index("query_id")["context_ids"]   # as the LLM read them
rerun = LexicalSearch(load_products()).run(load_queries("test"), k=5)                 # ties by product_id
differ = [q for q in stored.index if stored[q] != rerun[q]]
print("bm25 contexts that differ from lib.lexical:", len(differ))
print("bm25 contexts that differ from lib.lexical only in order:", sum(set(stored[q]) == set(rerun[q]) for q in differ))

scores = score_answers(answers, qrels("test"))            # one row per test query and context, on human grades
for context, rows in scores.groupby("context", sort=False):
    held, nothing = rows["exact in context"] > 0, rows["cited"] == 0
    print(f"{context}, unjudged products in the contexts: {rows['unjudged in context'].sum()}")
    print(f"{context}, contexts with an exact product: {held.sum()}")
    print(f"{context}, answers that cite an exact product: {(rows['exact cited'] > 0).sum()}")
    print(f"{context}, products cited: {rows['cited'].sum()}")
    print(f"{context}, cited products that are exact: {rows['exact cited'].sum()}")
    print(f"{context}, mean exact share: {rows['exact share'].mean():.3f}")
    print(f"{context}, answers that recommend nothing: {nothing.sum()}")
    print(f"{context}, recommend nothing, with an exact product in the context: {(nothing & held).sum()}")
    print(f"{context}, recommend something, with no exact product in the context: {(~nothing & ~held).sum()}")
    near = rows[~held]                                    # answers whose context held no exact product
    print(f"{context}, products cited with no exact product in the context: {near['cited'].sum()}")
    print(f"{context}, of those, partial: {near['partial cited'].sum()}")
    print(f"{context}, unjudged products cited: {rows['unjudged cited'].sum()}")
print("answers that cite more exact products than their context holds:",
      (scores["exact cited"] > scores["exact in context"]).sum())

print("planned test comparisons:", len(PLANNED_TEST_COMPARISONS))
print(f"p-value threshold: {THRESHOLD:.3f}")
share = scores.pivot(index="query_id", columns="context", values="exact share")
report_planned("answers, semantic over bm25", share["semantic"], share["bm25"])
