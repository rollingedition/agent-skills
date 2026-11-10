from lib.lexical import LexicalSearch
from lib.lexical_by_hand import tokenize
from lib.metrics import ndcg_at_k
from lib.queries import INCH_SPELLINGS, normalize_units, unit_rules
from lib.store import load_products, load_queries, product_text, qrels

products, queries, judgments = load_products(), load_queries(), qrels()
text = product_text(products).str.lower()
for name, unit in [("''", r"''"), ('"', r"\""), ("inch", r"-?inch")]:
    print(f"products that write a number then {name}:", text.str.contains(rf"\d\s*{unit}").sum())

first_try = unit_rules([spelling for spelling in INCH_SPELLINGS if spelling != "''"])   # written from queries
rules = {"as written": None, "first try": first_try, "normalized": unit_rules()}
checks = [("3.7-quart slow cooker", "normalized"), ("3 in 1 sofa bed", "normalized"), ("1 in twin", "normalized"),
          ("48 '' range hood", "first try"), ("48 '' range hood", "normalized")]
for example, name in checks:                                                   # what the tokenizer reads
    print(f"terms of {example}, {name}:", " ".join(tokenize(normalize_units(example, rules[name]))))

searches = {}
for name, rule in rules.items():
    rewritten = products.copy()
    if rule is not None:
        for column in ["name", "product_class", "category", "description"]:   # the columns product_text joins
            rewritten[column] = rewritten[column].map(lambda value: normalize_units(value, rule))
    searches[name] = LexicalSearch(rewritten)

with_units = queries[queries["query"].str.contains(r"\d\s*(?:qt|in\b|inch|\")")]
print("queries with a unit:", len(with_units))
print("of them, test queries:", (with_units["split"] == "test").sum())
for query_id, query in with_units["query"].items():
    label = f"{query_id} ({queries.at[query_id, 'split']})"
    print(f"{label}: {query} -> {normalize_units(query)}")
    for name, rule in rules.items():
        typed = query if rule is None else normalize_units(query, rule)
        ranking = list(searches[name].search(typed, k=10).index)
        print(f"{label}, bm25 ndcg@10 {name}: {ndcg_at_k(ranking, judgments[query_id], 10):.3f}")
