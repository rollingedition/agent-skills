"""Sorts each section ID that a reply cites into one outcome, for three recordings, over the dev items.

The outcomes are supported (listed by the item for its asked version), unlisted (a section of the asked version that the
item does not list), wrong-version (a section of another version only) and missing (a section of no version). The
check reads IDs, not sentences: whether a listed section supports the sentence is the judge's job, in grounded-answers.

An ID that exists in two versions cannot be told apart by the reply, because the citation carries no version. It is
judged against the asked version, so an ID shared by both versions is never wrong-version."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.contract import CITATION_OUTCOMES, citation_outcomes, parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256, P2_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

RECORDINGS = (  # label, recording, the sha256 of the prompt it was made from
    ("baseline", "assistant-baseline", P1_SHA256),
    ("unfiltered", "assistant-unfiltered", P1_SHA256),  # same prompt; retrieval from every version, versions shown
    ("prompt-b", "assistant-prompt-b", P2_SHA256),
)

ids = section_ids_by_version()
items = load_items(split="dev")  # dev only: held-out items are not read here (plan section 3.4)

for label, recording, prompt_sha256 in RECORDINGS:
    model = ReplayModel(recording, prompt_sha256)
    counts = Counter()
    for item in items:
        reply = parse_reply(model.reply(item.id, 0))
        # The item's list for its asked version. An unanswerable item may also list another version: not counted here.
        listed = frozenset(s.section_id for s in item.supporting_sections if s.version == item.version)
        counts.update(citation_outcomes(reply, item.version, listed, ids))
    total = sum(counts.values())
    print(f"{label} citations on dev items: {total}")
    for outcome in CITATION_OUTCOMES:
        print(f"{label} {outcome}: {pct(counts[outcome], total)}")
