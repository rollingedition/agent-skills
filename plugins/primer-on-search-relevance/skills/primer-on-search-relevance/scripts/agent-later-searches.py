"""Counts the words each later search adds to the agent's query so far, and how many of those the tool had already
shown. The point rests on the "words the tool had shown" line for each tool."""
from lib.generation import shown, words
from lib.recorded import agent_traces
from lib.store import load_products, load_queries

products, queries = load_products(), load_queries("test")
for tool in ["bm25", "semantic"]:
    later = new = from_results = 0
    for trace in (t for t in agent_traces() if t["retriever"] == tool):
        # words are lowercase runs of letters and digits, so case and punctuation don't count
        asked, seen = words(queries.at[trace["query_id"], "query"]), set()
        for number, search in enumerate(trace["searches"]):
            if number > 0:                                    # a later search: the words it adds, and where from
                added = words(search["query"]) - asked
                later, new, from_results = later + 1, new + len(added), from_results + len(added & seen)
            # every word the agent has searched so far
            asked |= words(search["query"])
            # what the tool showed for that search: name, class and attributes, but no description
            seen |= words(shown(search["results"], products))
    print(f"{tool}, later searches: {later}")
    print(f"{tool}, words that later searches add: {new}")
    print(f"{tool}, of those, words the tool had shown: {from_results}")
