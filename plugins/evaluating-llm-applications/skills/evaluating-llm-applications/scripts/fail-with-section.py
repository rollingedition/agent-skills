"""The dev items the baseline failed although a listed section of the asked version was in its top k, split into declines and answers.

For each answer it prints whether the reply cites a listed section, and the faithfulness judge's verdict on it. A decline has no
faithfulness verdict, because the judge reads only answers. An unreadable verdict is printed and left out, never counted as a fail."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import re

from lib.answers import Assistant
from lib.calibration import readable_verdicts
from lib.contract import citation_outcomes, parse_reply, section_ids_by_version
from lib.prompts import FAITH_SHA256, P1_SHA256, P1_SYSTEM, REF_SHA256
from lib.replay import ReplayModel
from lib.testset import load_items

RECORDING = "assistant-baseline"
k = ReplayModel(RECORDING, P1_SHA256).manifest["k"]  # the baseline's top k, as in retrieval-path
assistant = Assistant(RECORDING, P1_SYSTEM, P1_SHA256, k=k)  # its retriever only
replies = ReplayModel(RECORDING, P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1
faith = ReplayModel("judge-faithfulness-baseline", FAITH_SHA256)
ids = section_ids_by_version()
VERDICT = re.compile(r"^VERDICT:\s*(SUPPORTED|UNSUPPORTED)$")


def listed(item):
    """The item's supporting section IDs in its asked version."""
    return frozenset(s.section_id for s in item.supporting_sections if s.version == item.version)


dev = load_items(split="dev")
verdicts, unreadable = readable_verdicts("judge-answers-baseline", [item.id for item in dev], REF_SHA256)
for item_id, first in unreadable:
    print(f'unreadable verdict, left out: {item_id} ("{first}")')
fails = [item for item in dev if verdicts.get(item.id) == "FAIL" and listed(item) & {s.section_id for s in assistant.sections(item)}]
declined = [item for item in fails if parse_reply(replies.reply(item.id, 0)).declined]
answered = [item for item in fails if item not in declined]
print(f"right section in the top {k}, FAIL, declined: {len(declined)}")
print(f"right section in the top {k}, FAIL, answered: {len(answered)}")
print(f"answered FAIL with the section, citing a listed section: "
      f"{sum('supported' in citation_outcomes(parse_reply(replies.reply(item.id, 0)), item.version, listed(item), ids) for item in answered)}")
judged = {}  # item id -> SUPPORTED, UNSUPPORTED or unreadable, for each answered fail
for item in answered:
    line = next((ln.strip().strip("*`").strip() for ln in faith.reply(item.id, 0).splitlines() if ln.strip()), "")
    match = VERDICT.match(line)
    judged[item.id] = match.group(1) if match else "unreadable"
print(f"answered FAIL with the section, faithfulness SUPPORTED: {sum(v == 'SUPPORTED' for v in judged.values())}")
print(f"answered FAIL with the section, faithfulness UNSUPPORTED: {sum(v == 'UNSUPPORTED' for v in judged.values())}")
print("  " + (", ".join(i for i, v in judged.items() if v == "UNSUPPORTED") or "none"))
print(f"answered FAIL with the section, faithfulness unreadable: {sum(v == 'unreadable' for v in judged.values())}")
