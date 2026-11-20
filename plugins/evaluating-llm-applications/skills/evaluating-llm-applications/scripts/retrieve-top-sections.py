"""Shows BM25 retrieval for one question (q-0007, version 1.1): the words kept, then the top three sections.

The sections come from the version's own index, ranked by score and then by section ID, so a tie has one order.
The tokeniser drops one-letter words, so the `3` of `3.5mm` is lost and only `5mm` is matched."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import bm25s

from lib.docs import load_sections
from lib.retrieval import Retriever
from lib.testset import load_items

item = next(item for item in load_items() if item.id == "q-0007")
print(f"question {item.id} (version {item.version}): {item.question}")

# The words the index actually matches on: the same tokeniser, stopwords and token pattern as lib.retrieval.
kept = bm25s.tokenize([item.question], stopwords="en", return_ids=False, show_progress=False)[0]
print(f"words kept for matching: {' '.join(kept)}")
dropped = bm25s.tokenize(["a 3.5mm jack"], stopwords="en", return_ids=False, show_progress=False)[0]
print(f"words kept from the text 'a 3.5mm jack': {' '.join(dropped)}")

hits = Retriever(load_sections(item.version)).retrieve(item.question, 3)  # top 3 of the version's index
for rank, hit in enumerate(hits, start=1):
    print(f"rank {rank}: {hit.section_id} | score {hit.score:.3f}")
