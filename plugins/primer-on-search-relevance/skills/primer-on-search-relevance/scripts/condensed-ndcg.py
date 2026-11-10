from lib.lexical import LexicalSearch
from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.significance import compare
from lib.store import load_products, load_queries, qrels

queries, judgments = load_queries("test"), qrels("test")
runs = {"bm25": LexicalSearch(load_products()).run(queries, k=100), "semantic": SemanticSearch().run(queries, k=100)}

standard, condensed = {}, {}
for name, run in runs.items():
    # condensed: drop every unjudged product, so the judged ones move up into the top 10
    judged_only = {query_id: [product_id for product_id in ranking if product_id in judgments[query_id]]
                   for query_id, ranking in run.items()}
    standard[name] = evaluate(run, judgments)["ndcg@10"]
    condensed[name] = evaluate(judged_only, judgments)["ndcg@10"]
    print(f"{name} ndcg@10: {standard[name].mean():.3f}")
    print(f"{name} condensed ndcg@10: {condensed[name].mean():.3f}")

gain = condensed["bm25"] - standard["bm25"]                   # bm25's change, per test query
print(f"bm25 ndcg@10 for outdoor light fixtures: {standard['bm25'][133]:.3f}")
print(f"bm25 condensed ndcg@10 for outdoor light fixtures: {condensed['bm25'][133]:.3f}")
print(f"share of bm25's gain from outdoor light fixtures and beach blue headboard: {gain[[133, 46]].sum() / gain.sum():.3f}")

lead, condensed_lead = standard["semantic"] - standard["bm25"], condensed["semantic"] - condensed["bm25"]
change = compare(condensed_lead, lead)                       # is the change in the lead more than noise? (exploratory)
print(f"semantic minus bm25: {lead.mean():.3f}")
print(f"semantic minus bm25, condensed: {condensed_lead.mean():.3f}")
print(f"change in the lead: {change['mean difference']:.3f}")
print(f"95% interval for the change: {change['ci low']:.3f} to {change['ci high']:.3f}")
print(f"t-test p for the change: {change['t-test p']:.3f}")
print(f"permutation p for the change: {change['permutation p']:.3f}")
condensed_test = compare(condensed["semantic"], condensed["bm25"])   # the condensed lead itself (exploratory)
print(f"t-test p for the condensed lead: {condensed_test['t-test p']:.3f}")
print(f"permutation p for the condensed lead: {condensed_test['permutation p']:.3f}")
