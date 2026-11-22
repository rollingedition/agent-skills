"""The secrets and records regressions for chapter 9's security review (findings SEC9-01 to SEC9-05, and SEC9-08), with no
model and no recording.

The attempts are in data/regressions/secrets.json: provenance rows run cite_provenance on a reply, label rows run the
access label on a document, visible and search rows run the role filter, and fill rows render the secrets-out system
prompt and look for the portal key and the hidden marker. Each verdict is asserted against the expected one.

Prints one verdict per attempt, sorted, by name only. Prints no key, marker or attack text.
"""
from unittest import mock

from lib import cases, defences, harness, regressions, retrieval, threat, tools  # lib first: threads and seeds are fixed here


def _provenance_kind(attempt: dict, world: cases.World) -> str:
    return "refused" if isinstance(defences.cite_provenance(attempt["text"]), harness.Refuse) else "allowed"


def _label_kind(attempt: dict, world: cases.World) -> str:
    return retrieval.label(attempt["doc"])


def _visible_kind(attempt: dict, world: cases.World) -> str:
    return f"{len(retrieval.visible(tools._json('documents.json')['documents'], attempt['user']))} visible"


def _search_kind(attempt: dict, world: cases.World) -> str:
    return "results" if retrieval.search(attempt["query"], attempt["user"]) else "no result"


def _fill_kind(attempt: dict, world: cases.World) -> str:
    template = (defences.PROMPTS / "assistant-system-secrets-out.md").read_text(encoding="utf-8")
    text = harness.system_text(template, attempt["acting_user"], world)
    return "value present" if any(v in text for v in (world.portal_key, world.internal_marker)) else "neither value"


def main():
    docs = tools._json("documents.json")["documents"]
    assert all(doc.get("source") in ("office", "external") for doc in docs), "a document has a source the labels do not name"
    regressions.RUNNERS.update({"provenance": _provenance_kind, "label": _label_kind, "visible": _visible_kind,
                                "search": _search_kind, "fill": _fill_kind})
    regressions.report(regressions.check("secrets", cases.load_world()))

    # SEC9-09: the check must count a prompt that holds only one of the two private values as holding private values.
    # The prompt is stood in for, so only the value named here is present; a prompt with neither must read as clean.
    world = cases.load_world()
    with mock.patch.object(harness, "prompt_text", return_value=world.portal_key):
        one_key = threat.holds_private_values(())
    with mock.patch.object(harness, "prompt_text", return_value="no private values here"):
        neither = threat.holds_private_values(())
    print(f"SEC9-09 prompt with the portal key only, holds private values: {'yes' if one_key else 'no'}")
    print(f"SEC9-09 prompt with neither value, holds private values: {'yes' if neither else 'no'}")
    assert one_key and not neither, "a prompt holding one private value reads as clean"


if __name__ == "__main__":
    main()
