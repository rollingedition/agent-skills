from lib.metrics import evaluate
from lib.semantic import SemanticSearch
from lib.store import load_queries, qrels

train, judgments = load_queries("train"), qrels("train")       # choose on train queries

# dims keeps the first dims numbers of every vector and rescales each to length 1 (lib.recorded).
for dims in [768, 256, 128]:
    semantic = SemanticSearch(dims=dims)
    scores = evaluate(semantic.run(train, k=100), judgments)
    print(f"{dims} dimensions, float32 bytes per product: {semantic.products[0].nbytes:,}")
    print(f"{dims} dimensions, ndcg@10: {scores['ndcg@10'].mean():.3f}")
    print(f"{dims} dimensions, judged@10: {scores['judged@10'].mean():.3f}")
    print()
