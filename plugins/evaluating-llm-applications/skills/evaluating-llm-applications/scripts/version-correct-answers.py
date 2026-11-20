"""Reads the 25 version-dependent items for two variants: whether the judge passed the answer for the asked version, and whether a
citation names a section that exists only in another version.

The judge's verdict for each variant is read from its own recording, and an unreadable verdict is printed and left out of the
pass rate, never counted as a fail. A declined reply has a verdict like any other reply, so it stays in the denominator; its
count is printed beside each rate. A wrong-version citation is counted per item, over every item, so a zero shows as 0 of 25.
The last lines list the items where the two variants disagree, to read item by item."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import readable_verdicts
from lib.contract import citation_outcomes, parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256, REF_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

ids = section_ids_by_version()  # every version's section IDs, so a section of another version is known as one
# label, the assistant's recording, the judge's recording of that assistant's replies
VARIANTS = (("baseline", "assistant-baseline", "judge-answers-baseline"), ("unfiltered", "assistant-unfiltered", "judge-answers-unfiltered"))
items = [item for item in load_items() if item.kind == "version-dependent"]
item_ids = [item.id for item in items]
listed = {item.id: frozenset(s.section_id for s in item.supporting_sections if s.version == item.version) for item in items}
verdict, wrong = {}, {}  # label -> {item id: PASS or FAIL, readable only}; label -> item ids with a wrong-version citation
for label, assistant, judge in VARIANTS:
    verdict[label], unreadable = readable_verdicts(judge, item_ids, REF_SHA256)
    for item_id, first in unreadable:
        print(f'{label} unreadable verdict, left out: {item_id} ("{first}")')
    replies = ReplayModel(assistant, P1_SHA256)
    wrong[label] = {item.id for item in items
                    if "wrong-version" in citation_outcomes(parse_reply(replies.reply(item.id, 0)), item.version, listed[item.id], ids)}
    for split in ("dev", "held-out"):
        split_items = [item for item in items if item.split == split]
        readable = [item.id for item in split_items if item.id in verdict[label]]
        passed = sum(verdict[label][item_id] == "PASS" for item_id in readable)
        print(f"{label} {split} version-dependent items: {len(split_items)}")
        print(f"{label} {split} declined replies, counted in the denominator: "
              f"{sum(parse_reply(replies.reply(item.id, 0)).declined for item in split_items)}")
        print(f"{label} {split} judged correct for the asked version: {pct(passed, len(readable))}")
        print(f"{label} {split} citing a wrong-version section: "
              f"{pct(sum(item.id in wrong[label] for item in split_items), len(split_items))}")
    print(f"{label} all version-dependent items citing a wrong-version section: {pct(len(wrong[label]), len(items))}")

both = [item_id for item_id in item_ids if item_id in verdict["baseline"] and item_id in verdict["unfiltered"]]
print(f"items with a readable verdict in both variants: {len(both)}")
differ = [i for i in both if verdict["baseline"][i] != verdict["unfiltered"][i]]
print(f"items where the verdicts differ: {len(differ)}")
print("  " + (", ".join(differ) or "none"))
flag_differ = [i for i in item_ids if (i in wrong["baseline"]) != (i in wrong["unfiltered"])]
print(f"items where the wrong-version flag differs: {len(flag_differ)}")
print("  " + (", ".join(flag_differ) or "none"))
