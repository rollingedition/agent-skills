from lib.generation import ids_in_text
from lib.recorded import rag_answers

answers = rag_answers()
outside = answers.apply(lambda a: [p for p in a["cited"] if p not in a["context_ids"]], axis=1)
repeated = answers["cited"].map(lambda cited: len(cited) != len(set(cited)))
written = answers.apply(lambda a: ids_in_text(a["answer"], a["context_ids"]), axis=1)   # IDs the text writes out
print("answers:", len(answers))
print("answers that cite an ID outside their context:", (outside.map(len) > 0).sum())
print("answers that cite one ID twice:", repeated.sum())
print("answers that cite nothing:", (answers["cited"].map(len) == 0).sum())
print("answers that cite more than three products:", (answers["cited"].map(len) > 3).sum())
print("answers whose text and cited IDs differ:", (written != answers["cited"].map(set)).sum())
