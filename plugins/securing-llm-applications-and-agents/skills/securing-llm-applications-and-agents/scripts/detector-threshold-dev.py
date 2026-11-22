"""The detector's threshold, picked on dev alone: the lowest grid value at which at most 1 dev benign record is
flagged. The benign texts are the office's distinct records, each once, split by record ID into dev and held-out.

The point rests on the pick line and the dev counts beside it, and on the list of benign records flagged at the pick:
a threshold is only as good as the benign records it was checked on, so the flagged ones are named.
"""
from lib import detector, report  # lib first: threads and seeds are fixed here


def main():
    # Which model ran, by repository and commit: the classifier is pinned in examples/models.toml, and its weights
    # are checked against the pinned SHA-256 each time the model loads.
    print(f"model: {detector.REPO}")
    print(f"model commit: {detector.REVISION}")
    print("model weights: model.safetensors, SHA-256 checked against the pin")

    dev_cases = detector.attack_carriers("dev")
    dev_records = detector.benign_split("dev")
    print(f"benign records, dev: {len(dev_records)}")
    print(f"benign records, held-out: {len(detector.benign_split('held-out'))}")
    # Scores of the injected carrier texts and of the benign records, in ID order.
    carrier = detector.score([text for _, text in dev_cases])
    benign = detector.score([text for _, _, text in dev_records])

    # The counts at every grid value, so a reader can see why the pick sits where it does. A text is flagged at a
    # threshold when its score is at or above it.
    for threshold in detector.GRID:
        print(f"dev injected flagged at {threshold:.2f}: {sum(s >= threshold for s in carrier)} of {len(carrier)}")
        print(f"dev benign flagged at {threshold:.2f}: {sum(s >= threshold for s in benign)} of {len(benign)}")

    pick = detector.pick_threshold(benign)
    # The rule has an answer on this grid; if none qualified, the book would have no threshold to report, and the
    # run should stop rather than print a made-up one.
    assert pick is not None, "no grid threshold leaves at most 1 dev benign record flagged"
    print(f"pick: {pick:.2f}")
    print(f"dev true positives at the pick: {sum(s >= pick for s in carrier)} of {len(carrier)}")
    print(f"dev false positives at the pick: {sum(s >= pick for s in benign)} of {len(benign)}")
    # Scores this close to the pick could cross it under a small change of model or input, so they are counted
    # beside the pick (Risk 6). The scores themselves are never printed.
    print(f"dev scores within 0.02 of the pick: {detector.near(carrier + benign, pick)} of {len(carrier) + len(benign)}")
    # The benign records flagged at the pick, by record ID and kind. Their text is never printed: a flagged record is
    # a real document the office holds, and the chapter discusses it by ID.
    for (record_id, kind, _), score in zip(dev_records, benign):
        if score >= pick:
            print(f"dev benign record flagged at the pick, {record_id}: kind {kind}")


if __name__ == "__main__":
    main()
