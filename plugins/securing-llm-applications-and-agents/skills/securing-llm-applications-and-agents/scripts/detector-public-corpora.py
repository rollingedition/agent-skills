"""The detector at the threshold dev picked, run once over two public prompt-injection corpora: the share of
injection rows it flags and the share of benign rows it flags in deepset, and the share of attack rows it flags in
gandalf (recall only), each with its interval.

The point rests on the deepset rate lines: the detector's rates on text it was not built for, at the dev threshold.
The corpora are scored once and are never used to pick the threshold.
"""
from lib import detector, report  # lib first: threads and seeds are fixed here


def main():
    print(f"model: {detector.REPO}")
    print(f"model commit: {detector.REVISION}")
    print("model weights: model.safetensors, SHA-256 checked against the pin")

    dev_records = detector.benign_split("dev")
    pick = detector.pick_threshold(detector.score([text for _, _, text in dev_records]))
    assert pick is not None, "no grid threshold leaves at most 1 dev benign record flagged"
    print(f"threshold, picked on dev: {pick:.2f}")

    # deepset: 60 injection rows and 56 benign rows, labelled 1 and 0 in the corpus.
    rows = detector.public_rows("deepset-prompt-injections")
    scores = detector.score([text for _, text, _ in rows])
    injected = [score >= pick for (_, _, label), score in zip(rows, scores) if label == 1]
    benign = [score >= pick for (_, _, label), score in zip(rows, scores) if label == 0]
    assert len(injected) == 60 and len(benign) == 56, "deepset is 60 injection rows and 56 benign rows"
    report.rate_lines("deepset injection rows flagged", injected)
    report.rate_lines("deepset benign rows flagged", benign)
    print(f"deepset scores within 0.02 of the threshold: {detector.near(scores, pick)} of {len(rows)}")

    # gandalf: 112 rows, all attacks, so only recall can be reported.
    rows = detector.public_rows("gandalf-ignore-instructions")
    assert all(label == 1 for _, _, label in rows), "gandalf is all attacks: only recall is reported"
    scores = detector.score([text for _, text, _ in rows])
    report.rate_lines("gandalf attack rows flagged (recall only)", [score >= pick for score in scores])
    print(f"gandalf scores within 0.02 of the threshold: {detector.near(scores, pick)} of {len(rows)}")

    # The classifier's training data may include these corpora. Neither the model card nor the corpus cards say so,
    # so the rates above may be optimistic; this line is printed so the reader sees the caveat with the numbers.
    print("training-data overlap: possible, not stated on the model card or the corpus cards")


if __name__ == "__main__":
    main()
