"""The two counts behind the version check, and the version-dependent items where the variants' verdicts differ, by split.

A wrong-version citation is one whose ID exists only in another version, so an ID that several versions share cannot be
attributed to one of them. This prints how many section IDs are found in one version only, then how many citations to the
version-dependent items name a shared ID, for each variant. The last lines list the items where the verdicts differ, by split."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter

from lib.calibration import readable_verdicts
from lib.contract import parse_reply, section_ids_by_version
from lib.prompts import P1_SHA256, REF_SHA256
from lib.replay import ReplayModel
from lib.stats import pct
from lib.testset import load_items

ids = section_ids_by_version()
shared = Counter(i for found in ids.values() for i in found)  # how many versions each section ID appears in
print("section IDs found in one version only, by version: "
      + ", ".join(f"{v} {sum(shared[i] == 1 for i in found)}" for v, found in ids.items()))
items = [item for item in load_items() if item.kind == "version-dependent"]
split_of = {item.id: item.split for item in items}
verdict = {}  # label -> {item id: PASS or FAIL}, readable only
for label, assistant, judge in (("baseline", "assistant-baseline", "judge-answers-baseline"),
                                ("unfiltered", "assistant-unfiltered", "judge-answers-unfiltered")):
    replies = ReplayModel(assistant, P1_SHA256)
    cited = [cid for item in items for cid in parse_reply(replies.reply(item.id, 0)).citations]
    print(f"{label} citations to a section ID found in more than one version: "
          f"{pct(sum(shared[cid] > 1 for cid in cited), len(cited))}")
    verdict[label], _ = readable_verdicts(judge, list(split_of), REF_SHA256)
differ = [i for i in verdict["baseline"] if i in verdict["unfiltered"] and verdict["baseline"][i] != verdict["unfiltered"][i]]
for split in ("dev", "held-out"):
    part = [i for i in differ if split_of[i] == split]
    print(f"{split} items where the verdicts differ: {len(part)}")
    print("  " + (", ".join(part) or "none"))
