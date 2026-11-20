"""Sets the baseline's judge verdict against whether a supporting section reached the top k, for each dev item that has one.

Retrieval is BM25 over the asked version, so it is the same on every run and needs no recording; k is the baseline's, read from
its manifest. The two diagonal cells are the expected pairs. The two off-diagonal cells are the ones to read: a pass without the
right section retrieved, and a fail with it retrieved. Unanswerable items are left out, since they have no section of their asked
version to retrieve; their count is printed. An unreadable verdict is printed and left out, never counted as a fail. A declined reply is counted in its cell like any
other reply; the count of declines is printed. The FAIL cell is split into declines and answers in fail-with-section."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant
from lib.calibration import readable_verdicts
from lib.contract import parse_reply
from lib.prompts import P1_SHA256, P1_SYSTEM, REF_SHA256
from lib.replay import ReplayModel
from lib.testset import load_items

RECORDING = "assistant-baseline"
k = ReplayModel(RECORDING, P1_SHA256).manifest["k"]  # the top k the baseline's prompt was built from, read from its manifest
assistant = Assistant(RECORDING, P1_SYSTEM, P1_SHA256, k=k)  # its retriever only; the recording is not read here
replies = ReplayModel(RECORDING, P1_SHA256)  # the baseline's replies, sample 0, made from prompt P1, for the decline check

dev = load_items(split="dev")
has_support = [item for item in dev if any(s.version == item.version for s in item.supporting_sections)]
print(f"top k: {k}")
print(f"dev items: {len(dev)}")
print(f"dev items with no supporting section of the asked version, left out: {len(dev) - len(has_support)}")

verdicts, unreadable = readable_verdicts("judge-answers-baseline", [item.id for item in has_support], REF_SHA256)
for item_id, first in unreadable:
    print(f'unreadable verdict, left out: {item_id} ("{first}")')

# Keyed by (retrieved, passed): the four cells of the 2 by 2 table, each a list of item ids in sorted order.
cells = {(True, True): [], (True, False): [], (False, True): [], (False, False): []}
declined = set()  # item ids whose reply is a decline; they sit in their cells like any other reply
for item in has_support:
    if item.id not in verdicts:
        continue
    listed = {s.section_id for s in item.supporting_sections if s.version == item.version}
    top = {section.section_id for section in assistant.sections(item)}  # the top k sections, by BM25 rank
    cells[(bool(listed & top), verdicts[item.id] == "PASS")].append(item.id)
    if parse_reply(replies.reply(item.id, 0)).declined:
        declined.add(item.id)

print(f"items in the table: {sum(len(ids) for ids in cells.values())}")
print(f"declined items in the table, counted in their cells: {len(declined)}")
print(f"right section in the top {k}, PASS: {len(cells[(True, True)])}")
print(f"right section in the top {k}, FAIL: {len(cells[(True, False)])}")
print(f"right section not in the top {k}, PASS: {len(cells[(False, True)])}")
print(f"right section not in the top {k}, FAIL: {len(cells[(False, False)])}")
print("passed without the right section retrieved: " + (", ".join(cells[(False, True)]) or "none"))
print("failed with the right section retrieved: " + (", ".join(cells[(True, False)]) or "none"))
