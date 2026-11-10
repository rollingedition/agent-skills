from lib.generation import shown, words
from lib.recorded import agent_traces
from lib.store import load_products, load_queries

products, queries = load_products(), load_queries("test")
for tool in ["bm25", "semantic"]:
    later = new = from_results = 0
    for trace in (t for t in agent_traces() if t["retriever"] == tool):
        asked, seen = words(queries.at[trace["query_id"], "query"]), set()
        for number, search in enumerate(trace["searches"]):
            if number > 0:                                    # a later search: the words it adds, and where from
                added = words(search["query"]) - asked
                later, new, from_results = later + 1, new + len(added), from_results + len(added & seen)
            asked |= words(search["query"])
            seen |= words(shown(search["results"], products))   # name, class and attributes, as the tool showed them
    print(f"{tool}, later searches: {later}")
    print(f"{tool}, words that later searches add: {new}")
    print(f"{tool}, of those, words the tool had shown: {from_results}")
