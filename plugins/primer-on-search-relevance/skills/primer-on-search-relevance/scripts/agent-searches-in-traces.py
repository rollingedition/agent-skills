from lib.lexical import LexicalSearch
from lib.recorded import agent_traces, manifest, rag_answers
from lib.store import load_products, load_queries

recording, queries = manifest("agent-trace"), load_queries("test")
print("tool description:", recording["prompts"]["tool"]["function"]["description"])
print("searches allowed:", recording["max_searches"])
traces = {(t["retriever"], t["query_id"]): t for t in agent_traces()}
print("traces:", len(traces))
first = {key: t["searches"][0]["query"] for key, t in traces.items()}
print("first searches the same under both tools:", sum(first[("bm25", q)] == first[("semantic", q)] for q in queries.index))
print("first searches that keep the query as typed:", sum(first[("bm25", q)] == queries.at[q, "query"] for q in queries.index))
for q in queries.index:
    if first[("bm25", q)] != queries.at[q, "query"]:
        print(f"first search for {queries.at[q, 'query']}: {first[('bm25', q)]}")
context = {(a.context, a.query_id): a.context_ids for a in rag_answers().itertuples()}
print("traces whose first search returns the answer recording's context:",
      sum(t["searches"][0]["results"] == context[key] for key, t in traces.items()))
for tool in ["bm25", "semantic"]:
    mine = [t for (retriever, _), t in traces.items() if retriever == tool]
    print(f"{tool}, searches: {sum(len(t['searches']) for t in mine)}")
    print(f"{tool}, traces with one search: {sum(len(t['searches']) == 1 for t in mine)}")

lexical, shown = LexicalSearch(load_products()), recording["results_shown"]
stored = [s for (tool, _), t in traces.items() if tool == "bm25" for s in t["searches"]]   # what the agent saw
rerun = [lexical.search(s["query"], shown).index.tolist() for s in stored]                  # ties by product_id
differ = [(s["results"], r) for s, r in zip(stored, rerun) if s["results"] != r]
print("bm25 searches whose results differ from lib.lexical:", len(differ))
print("bm25 searches whose results differ from lib.lexical only in order:", sum(set(a) == set(b) for a, b in differ))
