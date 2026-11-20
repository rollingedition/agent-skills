"""Prints the twenty chapter items in id order: version, kind, planted flag and question, then the counts by kind.

The counts are the set's make-up that the chapter describes (plan section 3.4)."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.answers import chapter_items

items = chapter_items()  # sorted by id
for item in items:
    twin = item.twin_of if item.twin_of else "none"
    planted = f"planted ({item.planted_why})" if item.planted else "not planted"
    print(f"{item.id} | version {item.version} | {item.kind} | {planted} | twin {twin} | {item.question}")

kinds = Counter(item.kind for item in items)
for kind in ("answerable", "unanswerable", "version-dependent", "ambiguous"):
    print(f"items of kind {kind}: {kinds[kind]}")
print(f"planted items: {sum(1 for item in items if item.planted)}")
print(f"items in the dev split: {sum(1 for item in items if item.split == 'dev')}")
