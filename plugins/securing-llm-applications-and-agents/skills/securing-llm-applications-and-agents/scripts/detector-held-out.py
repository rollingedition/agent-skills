"""The detector at the threshold dev picked, scored once on the held-out half: how many injected texts it flags
(true positives) and how many held-out benign records it flags (false positives), each with its interval; then the
counts per style and per location, and the benign flags per record kind.

The point rests on the two rate lines: the held-out numbers are reported once, at the dev threshold, which is
recomputed here by the same rule and never typed in.
"""
from lib import detector, report  # lib first: threads and seeds are fixed here


def main():
    print(f"model: {detector.REPO}")
    print(f"model commit: {detector.REVISION}")
    print("model weights: model.safetensors, SHA-256 checked against the pin")

    # The threshold comes from dev alone, by the rule in plan section 21, so this example and the dev example
    # agree by construction.
    dev_records = detector.benign_split("dev")
    pick = detector.pick_threshold(detector.score([text for _, _, text in dev_records]))
    assert pick is not None, "no grid threshold leaves at most 1 dev benign record flagged"
    print(f"threshold, picked on dev: {pick:.2f}")

    cases_held = detector.attack_carriers("held-out")
    records = detector.benign_split("held-out")
    print(f"held-out injected texts: {len(cases_held)}")
    print(f"held-out benign records: {len(records)}")
    carrier = detector.score([text for _, text in cases_held])
    benign = detector.score([text for _, _, text in records])

    # A text is flagged when its score is at or above the threshold.
    injected_flags = [score >= pick for score in carrier]
    benign_flags = [score >= pick for score in benign]
    # The two rates, each with its bootstrap interval: true positives over the injected texts, false positives over
    # the benign records.
    report.rate_lines("held-out true positives, injected texts flagged", injected_flags)
    report.rate_lines("held-out false positives, benign records flagged", benign_flags)
    print(f"held-out scores within 0.02 of the threshold: {detector.near(carrier + benign, pick)} of {len(carrier) + len(benign)}")

    # Injected counts per style and per location, as counts only: a cell with a handful of cases is too thin for a
    # rate. Each row is a value, its flagged count and its total, sorted by value.
    indexes = range(len(cases_held))
    for label, key in (("style", lambda i: cases_held[i][0].style), ("location", lambda i: cases_held[i][0].location)):
        report.print_counts(f"held-out injected flagged, {label}", report.count_by(indexes, key, lambda i: injected_flags[i]))
    # Benign flags per record kind, the same way.
    benign_indexes = range(len(records))
    report.print_counts("held-out benign flagged, kind",
                        report.count_by(benign_indexes, lambda i: records[i][1], lambda i: benign_flags[i]))
    # The benign records flagged at the pick, by record ID and kind, never their text (plan section 21).
    for (record_id, kind, _), flagged in zip(records, benign_flags):
        if flagged:
            print(f"held-out benign record flagged at the pick, {record_id}: kind {kind}")


if __name__ == "__main__":
    main()
