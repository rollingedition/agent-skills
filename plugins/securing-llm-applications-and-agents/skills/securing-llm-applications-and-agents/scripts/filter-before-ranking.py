"""Filtering by access before ranking gives a staff user the same results as an index of only the documents they may read.

The point rests on the comparison of the result lists: filtering before ranking matches the visible-only index, and
filtering the top k after ranking moves the scores, because the hidden documents still count in IDF. No recording.
"""
from lib import cases, retrieval, tools  # lib first: threads and seeds are fixed here

import bm25s
import json

USER = "u-02"  # a staff member: public and staff documents are visible, owner-only ones are not
QUERIES = ("spare key deposit", "key handover", "standard deposit")  # fixed: the words of tasks t-13 and t-15
KS = (5, 2)  # the search's default page, and a short page where a hidden document can take a place
DOCS = json.loads((cases.DATA / "documents.json").read_text(encoding="utf-8"))["documents"]


def scores(query, rows):
    """BM25 score per document ID over these rows, scored the way tools.search_documents scores them."""
    key = tuple(sorted((d["doc_id"], d["title"], d["text"]) for d in rows))
    words = bm25s.tokenize([query], stopwords="en", return_ids=False, show_progress=False)[0]
    raw = tools._index(key).get_scores(words)  # the index for exactly these rows: IDF comes from them
    return {key[i][0]: round(float(raw[i]), 2) for i in range(len(key)) if raw[i] > 0}


def ranked(found, k):
    """The best k IDs by (-score, doc ID), the order search_documents uses."""
    return sorted(found, key=lambda d: (-found[d], d))[:k]


def main():
    visible = retrieval.visible(DOCS, USER)
    visible_ids = {d["doc_id"] for d in visible}
    print(f"documents visible to the user: {len(visible_ids)} of {len(DOCS)}")
    lost = moved = 0  # documents filtering after ranking lost at the short page; scores that moved
    for k in KS:
        for query in QUERIES:
            # Filter before ranking: the search the assistant runs, whose index holds visible documents only.
            before = [d["doc_id"] for d in retrieval.search(query, USER, k=k)]
            visible_only = scores(query, visible)  # the visible-only index, scored directly
            # Filter after ranking: rank every document, keep the top k, then drop the ones the user may not read.
            full = scores(query, DOCS)
            after = [d for d in ranked(full, k) if d in visible_ids]
            changed = sum(full[d] != visible_only.get(d) for d in after)  # IDF counts the hidden documents too
            print(f"k {k}, query {query!r}, filter before ranking, results: {len(before)}")
            print(f"k {k}, query {query!r}, filter after ranking, results: {len(after)}")
            print(f"k {k}, query {query!r}, filter after ranking, scores that differ: {changed} of {len(after)}")
            # The claims: the order matches the visible-only index, and no hidden document is returned.
            assert before == ranked(visible_only, k), f"k {k}, query {query!r}: order differs from the visible-only index"
            assert set(before) <= visible_ids, f"k {k}, query {query!r}: a hidden document was returned"
            # On these queries filtering after ranking also gives the same documents in the same order, and the same count.
            assert after == before, f"k {k}, query {query!r}: filtering after ranking changed the results"
            lost += (k == KS[-1]) * (len(before) - len(after))
            moved += changed
    print(f"short page, documents lost by filtering after ranking: {lost}")
    assert moved > 0, "no score moved, so the hidden documents did not count in IDF"


if __name__ == "__main__":
    main()
