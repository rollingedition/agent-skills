"""Runs the citation and format checks on the baseline replies to the twenty chapter items, and counts each problem.

A citation is a problem when its section was not in the item's prompt, which covers a section of another version."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.contract import PROBLEMS, format_problems, parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256, P1_SYSTEM
from lib.stats import pct

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)
items = chapter_items()
counts = {name: 0 for name in PROBLEMS}  # items with each problem, by its fixed name
items_with_problems = 0
answered = 0
answered_uncited = 0
citations = 0
citations_outside = 0  # cited IDs that were not in the item's prompt
for item in items:
    reply = assistant.reply(item)
    problems = format_problems(reply, context_ids=assistant.context_ids(item), expect_decline=item.kind == "unanswerable")
    items_with_problems += bool(problems)
    for name in problems:
        counts[name] += 1
    if not reply.declined and reply.text:
        answered += 1
        answered_uncited += not reply.citations
    citations += len(reply.citations)
    citations_outside += sum(1 for cid in reply.citations if cid not in assistant.context_ids(item))
assert citations_outside == 0, "every citation must point at a section that was in its item's prompt"
# A zero rate shows nothing unless the check can fire: a 1.1 section cited for a 2.0 item must be flagged as unknown.
planted_item = next(item for item in items if item.version == "2.0")
planted = sorted(section_ids_by_version()["1.1"] - assistant.context_ids(planted_item))[0]
planted_problems = format_problems(parse_reply(f"Yes. [sec:{planted}]"), context_ids=assistant.context_ids(planted_item), expect_decline=False)
assert "unknown-section" in planted_problems, "the check must fire on a planted bad citation"

print(f"items: {len(items)}")
print(f"items with a format problem: {pct(items_with_problems, len(items))}")
for name in sorted(counts):  # sorted by problem name
    print(f"items with problem {name}: {counts[name]}")
print(f"answered items: {answered}")
print(f"answered items with no citation: {pct(answered_uncited, answered)}")
print(f"citations: {citations}")
print(f"citations to a section not in the prompt: {pct(citations_outside, citations)}")
