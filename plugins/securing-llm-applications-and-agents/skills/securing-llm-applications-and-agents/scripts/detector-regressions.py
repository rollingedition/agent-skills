"""The detector filter's regressions for chapter 5's security review (findings S5-1 to S5-4 and S5-6), with no generative
model. The classifier runs on this machine's CPU.

The attempts are in data/regressions/detector.json. Each one places an injection from the dev split in a tool result
(a long benign prefix before it, a slot's start field, a slot note as an object, an inbox sender field), or a benign text
with paragraph breaks and quotes. The injection text comes from the case data at run time, so no attack string is in
any file here. Each verdict is asserted against the expected one: withheld, or passed.

Prints one verdict per attempt, by name only. Prints no injection, prefix or attack text.
"""
import json
from pathlib import Path

from lib import cases, defences, detector, regressions, tools  # lib first: threads and seeds are fixed here

ATTEMPTS = Path(__file__).resolve().parent / "data" / "regressions" / "detector.json"


def main():
    dev = [case.injection for case in cases.load_cases("dev")]
    pick = detector.pick_threshold(detector.score([text for _, _, text in detector.benign_split("dev")]))
    assert pick is not None, "no grid threshold leaves at most 1 dev benign record flagged"
    # The injections the filter withholds on their own at the pick, in ID order: an attempt tests a placement, not a
    # miss that the injection itself would already have.
    withheld = [text for text, score in zip(dev, detector.score(dev)) if score >= pick]
    prefix = regressions.benign_prefix(detector.benign_records())
    hook = defences.detector_filter(pick)
    attempts = json.loads(ATTEMPTS.read_text(encoding="utf-8"))["attempts"]
    verdicts = {}
    for attempt in attempts:
        injection = withheld[attempt["index"]] if attempt["source"] == "dev-withheld" else ""
        data = regressions.attempt_result(attempt["placement"], injection, prefix)
        out = hook(
            {"name": "read_message"}, tools.ToolResult(data)
        )
        verdict = "withheld" if out.data == dict(defences.WITHHELD) else "passed"
        verdicts[attempt["name"]] = (verdict, attempt["expected"])
    for name in sorted(verdicts):
        verdict, expected = verdicts[name]
        print(f"{verdict:<9} {name}")
        assert verdict == expected, f"{name}: the filter {verdict}, expected {expected}"
    print(f"attempts: {len(verdicts)}, as expected: {sum(v == e for v, e in verdicts.values())}")
    print(f"threshold, picked on dev: {pick:.2f}")


if __name__ == "__main__":
    main()
