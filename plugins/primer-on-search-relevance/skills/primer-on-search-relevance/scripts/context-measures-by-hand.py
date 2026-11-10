from lib import generation
from lib.generation import EXACT
from lib.metrics import precision_at_k, recall_at_k
from lib.recorded import rag_answers
from lib.store import load_queries, qrels


def context_precision(context, judged, k=5):
    """Ragas's context precision, with the judges as the reference: mean precision@i over exact positions i."""
    hits = [i for i, p in enumerate(context[:k], start=1) if judged.get(p, 0) == EXACT]
    return sum(precision_at_k(context, judged, i) for i in hits) / len(hits) if hits else 0.0


def context_recall(context, judged, k=5):
    """Ragas's ID-based context recall: the share of the reference IDs that the context holds."""
    reference = {p for p, grade in judged.items() if grade == EXACT}
    return len(reference & set(context[:k])) / len(reference)


judgments, queries = qrels("test"), load_queries("test")
answers = rag_answers().query("context != 'random'")             # the two retrievers' contexts for each test query
contexts = [(answer.context_ids, judgments[answer.query_id]) for answer in answers.itertuples()]
print("contexts:", len(contexts))
same = {"recall_at_k": all(context_recall(c, j) == recall_at_k(c, j, 5) for c, j in contexts),
        "lib.generation": all(context_precision(c, j) == generation.context_precision(c, j) for c, j in contexts)}
print("context recall equals recall_at_k every time:", "yes" if same["recall_at_k"] else "no")
print("context precision equals lib.generation's every time:", "yes" if same["lib.generation"] else "no")

first = answers.iloc[0]                                          # one context, worked through
context, judged = first["context_ids"], judgments[first["query_id"]]
print(f"grades in order, {queries.at[first['query_id'], 'query']}, {first['context']}:", *[judged.get(p, 0) for p in context])
print(f"context precision@5: {context_precision(context, judged):.3f}")
print(f"precision@5: {precision_at_k(context, judged, 5):.3f}")
exact = sorted(sum(grade == EXACT for grade in grades.values()) for grades in judgments.values())
print(f"exact products judged per test query: {exact[0]} to {exact[-1]}")
print(f"highest recall@5 possible for the query with the most: {5 / exact[-1]:.3f}")
