"""The isolation regressions for chapter 8's security review (findings S8-1 to S8-3), with no model and no recording.

The rows are in data/regressions/isolation.json. A taint row checks one outbound call against the provenance built from
its results and third-party tool definitions. A plan row runs one plan through the plan-then-execute hooks, the way the
harness does, and reports the first verdict. Rows marked open are pinned at a gap the review found and not yet fixed.

Prints one verdict per attempt, sorted, by name only. Prints no phone numbers, keys or attack text.
"""
from lib import cases, regressions  # lib first: threads and seeds are fixed here

# P13c: a text placeholder (the model's own words) in book_visit.slot_id. Only a message body may take model text, so
# the plan must be refused before the booking runs. The control is a slot_id taken from list_slots, which is allowed.
TEXT_SLOT = [
    {"name": "read_message", "arguments": {"msg_id": "msg-07"}},
    {"name": "book_visit", "arguments": {"contractor_id": "brk-01", "ticket_id": "T-1",
                                         "slot_id": {"type": "text", "from": 0, "field": "body"}}},
]
TYPED_SLOT = [
    {"name": "list_slots", "arguments": {"contractor_id": "brk-01", "date_from": "2026-01-01", "date_to": "2026-12-31"}},
    # the slot is the one list_slots gives for 2026-12-01 at 09:00: the placeholder picks the single item that matches
    {"name": "book_visit", "arguments": {"contractor_id": "brk-01", "ticket_id": "T-1",
                                         "slot_id": {"type": "slot_id", "from": 0, "field": "slots.slot_id",
                                                     "where": {"start": "2026-12-01T09:00"}}}},
]


def main():
    world = cases.load_world()
    regressions.report(regressions.check("isolation", world))

    text = regressions.RUNNERS["plan-call"]({"acting_user": "u-02", "plan": TEXT_SLOT}, world)
    control = regressions.RUNNERS["plan-call"]({"acting_user": "u-02", "plan": TYPED_SLOT}, world)  # control: allowed
    print(f"P13c text placeholder in book_visit.slot_id: {text}")
    print(f"P13c control, slot_id from list_slots: {control}")
    assert text == "refused", "a model's text reaches book_visit.slot_id"
    assert control == "allowed", "the control slot_id from list_slots was refused"


if __name__ == "__main__":
    main()
