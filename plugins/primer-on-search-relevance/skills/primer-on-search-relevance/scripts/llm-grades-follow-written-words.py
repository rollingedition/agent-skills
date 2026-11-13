"""Checks whether the LLM's grades follow the words in each product's text, for one train pair, for the clear shower curtain products, and across both pools. The prose's point rests on the 'share graded lower' and 'share graded higher' lines, which compare pairs whose text has every query word with pairs that miss one."""
import re

from lib.agreement import PROMPTS, as_the_llm_saw, graded_pairs
from lib.store import load_products, load_queries


def words(text):
    """Lowercase word tokens, as chapter 2 matches query words against product text."""
    # runs of letters, digits and underscores, so 7qt is one word and '7 qt' is two
    return set(re.findall(r"\w+", text.lower()))


products, queries = load_products(), load_queries()
# query 163 is a train query, and product 20718 is the pair the prose follows
print("query:", queries.at[163, "query"])                              # a train query
print(as_the_llm_saw(products.loc[20718]))
print("grades from people, short, guidelines:", *graded_pairs("train").set_index(["query_id", "product_id"]).loc[(163, 20718)])

curtains = graded_pairs("test").query("query_id == 246")      # clear shower curtain: every product in a top 10
# whole words only, so 'unclear' doesn't count as saying clear
says = curtains["product_id"].map(lambda product_id: "clear" in words(as_the_llm_saw(products.loc[product_id])))
for kind, group in [("say clear", curtains[says]), ("never say clear", curtains[~says])]:
    print(f"\nclear shower curtain products that {kind}: {len(group)}")
    for column, judge in [("human", "people"), ("short", "the short prompt"), ("guidelines", "the guidelines prompt")]:
        print(f"products that {kind}, graded exact by {judge}: {(group[column] == 2).sum()}")

for pool in ["train", "test"]:
    pairs = graded_pairs(pool).dropna(subset=["human"])                     # in the test pool, the pairs people judged
    # subset: every query word appears in the text the LLM saw
    pairs["every word"] = [words(queries.at[query_id, "query"]) <= words(as_the_llm_saw(products.loc[product_id]))
                           for query_id, product_id in zip(pairs["query_id"], pairs["product_id"])]
    # share of each group that the LLM grades below people (exact) or above them (partial), for each prompt
    for label, grade, every_word, direction in [("exact", 2, False, "lower"), ("exact", 2, True, "lower"),
                                                ("partial", 1, True, "higher"), ("partial", 1, False, "higher")]:
        group = pairs[(pairs["human"] == grade) & (pairs["every word"] == every_word)]
        kind = f"{label} {pool} pairs {'with every query word' if every_word else 'missing a query word'}"
        print(f"\n{kind}: {len(group)}")
        for prompt in PROMPTS:
            moved = group[prompt] < grade if direction == "lower" else group[prompt] > grade
            print(f"share graded {direction}, {prompt} prompt, {kind}: {moved.mean():.3f}")
