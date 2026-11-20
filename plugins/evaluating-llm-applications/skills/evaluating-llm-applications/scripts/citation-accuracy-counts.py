"""Counts the baseline's answered items that cite a supporting section of the asked version, dev and held-out apart.

An item counts once, and only if one of its citations is supported; its other citations sit in the citation lines. A decline
is not an answer, so it is left out of every count. The check matches each cited ID against the item's listed supporting
section IDs for its asked version. It never reads the section's text, so it does not check what the sentence says.
The first line of each split is the point: the item rate."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import citation_outcomes, parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

ids = section_ids_by_version()  # every version's section IDs, read from the docs, for telling wrong-version from missing
model = ReplayModel("assistant-baseline", P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1


def supporting_ids(item):
    """The item's supporting section IDs in its asked version. Another version's listed sections are not counted here."""
    return frozenset(s.section_id for s in item.supporting_sections if s.version == item.version)


for split in ("dev", "held-out"):
    declined = 0
    results = {}  # item id -> its citation outcomes, for each answered item
    for item in load_items(split=split):
        reply = parse_reply(model.reply(item.id, 0))
        if reply.declined:
            declined += 1
        else:
            results[item.id] = citation_outcomes(reply, item.version, supporting_ids(item), ids)
    # An answer to an unanswerable item lists no section of its asked version, so it can never count as supported here.
    outcomes = [outcome for found in results.values() for outcome in found]  # every citation, in item order
    with_support = [item_id for item_id, found in results.items() if "supported" in found]
    no_support = sorted(set(results) - set(with_support))
    print(f"{split} declined items, left out: {declined}")
    print(f"{split} answered items: {len(results)}")
    print(f"{split} answered items citing a supporting section of the asked version: {pct(len(with_support), len(results))}")
    print(f"{split} answered items with no supported citation: {len(no_support)}")
    print("  " + (", ".join(no_support) or "none"))
    print(f"{split} citations: {len(outcomes)}")
    print(f"{split} citations that are supported: {pct(outcomes.count('supported'), len(outcomes))}")
    print(f"{split} citations that are unlisted: {pct(outcomes.count('unlisted'), len(outcomes))}")
    print(f"{split} citations that are wrong-version or missing: "
          f"{pct(outcomes.count('wrong-version') + outcomes.count('missing'), len(outcomes))}")
