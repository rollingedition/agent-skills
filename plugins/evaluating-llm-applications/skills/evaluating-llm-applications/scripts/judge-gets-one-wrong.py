"""Shows one judge verdict that breaks the judge's own rule: on q-0019, the judge passes P2's reply, which answers only one of the
two readings in the reference. The rule it breaks is rule 3 of the judge's prompt, printed below from that prompt.

The hand verdict is a person's reading, written into this file. It is printed beside the judge's verdict and is the only
number here that is not a recorded one; the count of passes with it is taken from the judge's own verdicts."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.judging import verdicts
from lib.prompts import P1_SHA256, P1_SYSTEM, P2_SHA256, P2_SYSTEM, REF_SYSTEM
from lib.replay import ReplayModel

ITEM_ID = "q-0019"
HAND = {"q-0019": "FAIL"}  # read by hand against rule 3: the reply answers reading 1 and not reading 2

item = next(item for item in chapter_items() if item.id == ITEM_ID)
print(f"question {item.id} (version {item.version}, {item.kind}, planted: {item.planted_why}): {item.question}")
print(f"reference answer: {item.reference_answer}")
print(f"P2 reply: {Assistant('assistant-prompt-b', P2_SYSTEM, P2_SHA256).reply(item).text}")

raw = ReplayModel("judge-answers-prompt-b", None).reply(item.id, 0)  # the judge's recorded reply to P2's answer
print(f"judge verdict on P2's reply: {verdicts('judge-answers-prompt-b', [item.id])[item.id]}")
reason = [line.strip() for line in raw.splitlines() if line.strip()][1:]  # the line after the verdict
print(f"judge reason: {reason[0] if reason else 'none'}")
print(f"judge verdict on P1's reply to the same item: {verdicts('judge-answers-baseline', [item.id])[item.id]}")
print(f"hand verdict on P2's reply, under rule 3: {HAND[item.id]}")
rule_3 = next(line for line in REF_SYSTEM.splitlines() if line.startswith("3. "))
print(f"rule it breaks: {rule_3}")

ids = [item.id for item in chapter_items()]
judged = verdicts("judge-answers-prompt-b", ids)
passes = sum(verdict == "PASS" for verdict in judged.values())
by_hand = passes - sum(1 for item_id in HAND if judged[item_id] == "PASS" and HAND[item_id] == "FAIL")
print(f"P2 passes, as judged: {passes} of {len(ids)}")
print(f"P2 passes, with {ITEM_ID} read by hand: {by_hand} of {len(ids)}")
