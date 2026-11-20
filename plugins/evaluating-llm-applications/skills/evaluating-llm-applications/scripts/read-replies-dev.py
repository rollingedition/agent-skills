"""Prints the dev items, grouped by kind and sorted by ID, with each item's reference answer and the baseline,
unfiltered and second-model replies.

The reference is printed in full under its item, since the reading compares each reply with it. Each reply is one line:
whether it declined, its citations, and its first 120 characters. The reader's job is to set these side by side and
see which failure each reply shows (the codes are in data/failure-codes.json)."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import DECLINE, parse_reply
from lib.prompts import P1_SHA256
from lib.replay import ReplayModel
from lib.testset import load_items

RECORDINGS = {  # the three variants, in the order the chapter discusses them
    "baseline": "assistant-baseline",
    "unfiltered": "assistant-unfiltered",
    "second-model": "assistant-second-model",
}
KINDS = ("answerable", "unanswerable", "version-dependent", "ambiguous")  # plan section 3.1 order
SHOWN = 120  # characters of each reply printed; the full text is in the recording

# The prompt hash is checked here, so a recording made from another prompt fails to load.
models = {name: ReplayModel(recording, P1_SHA256) for name, recording in RECORDINGS.items()}
items = load_items(split="dev")  # dev only: the held-out items are not read in this chapter (plan section 3.4)

for kind in KINDS:
    group = [item for item in items if item.kind == kind]  # load_items already sorts by ID
    print(f"## {kind}: {len(group)} dev items")
    for item in group:
        planted = f"planted ({item.planted_why})" if item.planted else "not planted"
        print(f"{item.id} | version {item.version} | {planted} | {item.question}")
        reference = item.reference_answer or "none: the item is unanswerable, so the right reply declines"
        print(f"  reference: {reference}")
        for name in RECORDINGS:
            reply = parse_reply(models[name].reply(item.id, 0))
            if reply.declined:
                mark = "declined"
            elif DECLINE in reply.text:
                # The phrase is there, but with other text: the parser does not call that a decline.
                mark = "decline phrase with other text"
            else:
                mark = f"cites {' '.join(reply.citations)}" if reply.citations else "no citation"
            text = reply.text.replace("\n", " ")  # a reply may hold line breaks; one line keeps the output readable
            more = "..." if len(text) > SHOWN else ""
            print(f"  {name} ({mark}): {text[:SHOWN]}{more}")
