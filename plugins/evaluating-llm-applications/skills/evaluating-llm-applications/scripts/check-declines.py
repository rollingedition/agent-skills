"""Counts the two decline errors over the baseline replies: answerable items declined, and unanswerable items answered.

Version-dependent and ambiguous items are left out of both rates: a version-dependent item is scored by its own rate,
version-correctness, and an ambiguous item has no rate yet. The last lines name any excluded item the baseline declined."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.prompts import P1_SHA256, P1_SYSTEM
from lib.stats import pct

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)
items = chapter_items()
answerable = [item for item in items if item.kind == "answerable"]
unanswerable = [item for item in items if item.kind == "unanswerable"]

false_refusals = [item.id for item in answerable if assistant.reply(item).declined]  # already in id order
false_answers = [item.id for item in unanswerable if not assistant.reply(item).declined]
print(f"answerable items: {len(answerable)}")
print(f"false refusal rate (answerable items declined): {pct(len(false_refusals), len(answerable))}")
for item_id in false_refusals:
    print(f"false refusal: {item_id}")
print(f"unanswerable items: {len(unanswerable)}")
print(f"false answer rate (unanswerable items answered): {pct(len(false_answers), len(unanswerable))}")
for item_id in false_answers:
    print(f"false answer: {item_id}")
print(f"items not counted here (version-dependent and ambiguous): {len(items) - len(answerable) - len(unanswerable)}")
excluded = [item for item in items if item.kind in ("version-dependent", "ambiguous")]
declined_excluded = [item.id for item in excluded if assistant.reply(item).declined]  # the decline is not counted
print(f"declined, not counted here: {', '.join(declined_excluded) or 'none'}")
