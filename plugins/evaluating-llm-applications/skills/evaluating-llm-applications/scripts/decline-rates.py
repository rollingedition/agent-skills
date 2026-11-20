"""Counts the two decline errors for each recording, on dev and on held-out: answerable items declined (false refusals)
and unanswerable items answered (false answers). Each rate line rests on its own count and denominator.

Version-dependent and ambiguous items are left out of both rates; the last line per split counts the declines among
them, which are not errors here."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import parse_reply
from lib.prompts import P1_SHA256, P2_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

VARIANTS = (  # label, recording, the sha256 of the prompt it was made from
    ("baseline", "assistant-baseline", P1_SHA256),  # P1, k=3, filtered to the asked version
    ("unfiltered", "assistant-unfiltered", P1_SHA256),  # P1, k=3, sections from every version
    ("prompt-b", "assistant-prompt-b", P2_SHA256),  # P2, k=3, filtered
    ("k5", "assistant-k5", P1_SHA256),  # P1, k=5, filtered
)

for label, recording, prompt_sha256 in VARIANTS:
    model = ReplayModel(recording, prompt_sha256)  # refuses a recording made from another prompt
    for split in ("dev", "held-out"):
        items = load_items(split=split)
        declined = {item.id: parse_reply(model.reply(item.id, 0)).declined for item in items}  # sample 0 only
        answerable = [item for item in items if item.kind == "answerable"]
        unanswerable = [item for item in items if item.kind == "unanswerable"]
        refused = sorted(item.id for item in answerable if declined[item.id])
        answered = sorted(item.id for item in unanswerable if not declined[item.id])
        other_kinds = ("version-dependent", "ambiguous")
        other = [item.id for item in items if item.kind in other_kinds and declined[item.id]]
        print(f"{label} {split} false refusal rate (answerable declined): {pct(len(refused), len(answerable))}")
        print(f"{label} {split} false refusals: {', '.join(refused) or 'none'}")
        print(f"{label} {split} false answer rate (unanswerable answered): {pct(len(answered), len(unanswerable))}")
        print(f"{label} {split} false answers: {', '.join(answered) or 'none'}")
        for item_id in answered:  # what each false answer cites, and its text, so the chapter's claims can be checked
            reply = parse_reply(model.reply(item_id, 0))
            print(f"{label} {split} reply to {item_id} cites: {', '.join(reply.citations) or 'none'}")
            print(f"{label} {split} reply to {item_id} text: {reply.text}")
        print(f"{label} {split} declined, not counted (version-dependent and ambiguous): {len(other)}")
