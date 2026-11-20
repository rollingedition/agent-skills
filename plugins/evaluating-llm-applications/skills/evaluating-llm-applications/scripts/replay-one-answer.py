"""Replays the recorded baseline reply to q-0006 and parses it: the sections it was given, the reply, its citations.

Nothing is generated here: the reply is the recorded text, read back as the same string."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.contract import format_problems
from lib.prompts import P1_SHA256, P1_SYSTEM

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)  # the prompt hash must match the manifest
item = next(item for item in chapter_items() if item.id == "q-0006")
print(f"question {item.id} (version {item.version}, {item.kind}): {item.question}")
for rank, section in enumerate(assistant.sections(item), start=1):  # the top 3, in rank order
    print(f"section in context, rank {rank}: {section.section_id}")

reply = assistant.reply(item)
print("recorded reply:")
print(reply.text)
print(f"citations, in order: {' '.join(reply.citations)}")
print(f"format problems: {', '.join(format_problems(reply, context_ids=assistant.context_ids(item), expect_decline=False)) or 'none'}")
# A reply to an answerable item must answer and cite; this is the one fact the prose relies on here.
assert reply.citations and not reply.declined, "q-0006 should be answered, with at least one citation"
