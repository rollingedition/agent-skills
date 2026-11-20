"""Runs the format check and the order check over the unfiltered and second-model replies to the dev items. The baseline
has no problem of either kind (format-problems-baseline), so these two recordings are where the checks fire.

Each name is also run once on a fixture reply built to break it, and the example stops if a name does not fire. A zero
on a real split then means the check found nothing, not that it could not fire. Held-out items are not read here."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant
from lib.contract import ORDER_PROBLEMS, PROBLEMS, format_problems, order_problems, parse_reply
from lib.prompts import P1_SHA256, P1_SYSTEM
from lib.testset import load_items

VARIANTS = (("unfiltered", "assistant-unfiltered"), ("second-model", "assistant-second-model"))
FIXTURE_IDS = frozenset({"example-start"})  # the one section a fixture may cite
FIXTURES = (  # name, reply text, whether the item must be declined
    ("empty", "", False),
    ("declined-with-text", "The docs don't say. [sec:example-start]", False),
    ("no-citation", "Run svc start to start the service.", False),
    ("unknown-section", "Run svc start to start the service. [sec:made-up]", False),
    ("answered-declined-expected", "Run svc start to start the service. [sec:example-start]", True),
    ("citation-first", "[sec:example-start] Start the service.\nRun svc start.", False),
    ("stray-line", "Run `svc start` [sec:example-start]\nService", False),
)

items = load_items(split="dev")
for label, recording in VARIANTS:
    assistant = Assistant(recording, P1_SYSTEM, P1_SHA256)
    found = {name: [] for name in (*PROBLEMS, *ORDER_PROBLEMS)}
    for item in items:
        reply = assistant.reply(item)
        for name in format_problems(reply, context_ids=assistant.context_ids(item), expect_decline=item.kind == "unanswerable"):
            found[name].append(item.id)
        for name in order_problems(reply.text):
            found[name].append(item.id)
    for name, ids in found.items():
        shown = f"{len(ids)} of {len(items)}" + (f" ({', '.join(ids)})" if ids else "")
        print(f"{label} {name}: {shown}")

for name, raw, must_decline in FIXTURES:
    reply = parse_reply(raw)
    fired = name in format_problems(reply, context_ids=FIXTURE_IDS, expect_decline=must_decline) or name in order_problems(reply.text)
    assert fired, f"the fixture for {name} does not fire the check"
    print(f"fixture {name}: fired")
