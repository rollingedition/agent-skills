"""Checks every recorded answer's cited IDs against its context, and its text against its cited field. The point
rests on the zero counts for IDs outside the context and for disagreeing text, and on the count of answers that
cite more than three products."""
from lib.generation import ids_in_text
from lib.recorded import rag_answers

answers = rag_answers()
outside = answers.apply(lambda a: [p for p in a["cited"] if p not in a["context_ids"]], axis=1)
# an ID cited twice makes the list longer than the set of its IDs
repeated = answers["cited"].map(lambda cited: len(cited) != len(set(cited)))
# the text is searched only for the context's IDs, so an ID from outside it can't match
written = answers.apply(lambda a: ids_in_text(a["answer"], a["context_ids"]), axis=1)   # IDs the text writes out
print("answers:", len(answers))
print("answers that cite an ID outside their context:", (outside.map(len) > 0).sum())
print("answers that cite one ID twice:", repeated.sum())
print("answers that cite nothing:", (answers["cited"].map(len) == 0).sum())
# the prompt asks for up to three products
print("answers that cite more than three products:", (answers["cited"].map(len) > 3).sum())
print("answers whose text and cited IDs differ:", (written != answers["cited"].map(set)).sum())
