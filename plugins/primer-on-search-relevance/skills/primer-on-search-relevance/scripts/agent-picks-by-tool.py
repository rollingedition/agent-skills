import pandas as pd

from lib.generation import EXACT, report_planned
from lib.metrics import precision_at_k
from lib.recorded import agent_traces
from lib.significance import compare
from lib.store import qrels

judgments, picks, top_three, below = qrels("test"), {}, {}, 0
for tool in ["bm25", "semantic"]:
    traces = [t for t in agent_traces() if t["retriever"] == tool]
    returned = [{p for search in t["searches"] for p in search["results"]} for t in traces]
    seen = [sum(judgments[t["query_id"]].get(p, 0) == EXACT for p in r) for t, r in zip(traces, returned)]
    picked = [sum(judgments[t["query_id"]].get(p, 0) == EXACT for p in t["picked"]) for t in traces]
    print(f"{tool}, picks the tool never returned: {sum(len(set(t['picked']) - r) for t, r in zip(traces, returned))}")
    print(f"{tool}, picks nobody judged: {sum(p not in judgments[t['query_id']] for t in traces for p in t['picked'])}")
    print(f"{tool}, traces with fewer than three picks: {sum(len(t['picked']) < 3 for t in traces)}")
    print(f"{tool}, traces whose searches returned no exact product: {sum(s == 0 for s in seen)}")
    print(f"{tool}, traces that saw an exact product and picked none: {sum(s > 0 and k == 0 for s, k in zip(seen, picked))}")
    picks[tool] = pd.Series({t["query_id"]: precision_at_k(t["picked"], judgments[t["query_id"]], 3) for t in traces})
    top_three[tool] = pd.Series({t["query_id"]: precision_at_k(t["searches"][0]["results"], judgments[t["query_id"]], 3)
                                 for t in traces})               # the tool's own top 3 for the first search
    print(f"{tool}, precision@3 of the picks: {picks[tool].mean():.3f}")
    print(f"{tool}, precision@3 of the first search's top 3: {top_three[tool].mean():.3f}")
    p_value = compare(picks[tool], top_three[tool])["permutation p"]
    print(f"{tool}, picks against the top 3, exploratory permutation p: {p_value:.3f}")
    below += p_value < 0.05

print(f"picks against the top 3, p-values below 0.05 uncorrected: {below} of 2")
report_planned("agent picks, semantic over bm25", picks["semantic"], picks["bm25"])
