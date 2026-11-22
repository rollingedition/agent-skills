"""The open model's yes-or-no verdicts as a detector, replayed from its recording: how many injected texts it flags and
how many benign texts it flags on dev, held-out and the public corpora, with its agreement with the labels on dev as the
calibration. The classifier at its dev threshold reads the held-out texts, for comparison.

The point rests on the dev agreement line, which says how far the judge's yes and no can be trusted, and on the paired
difference between the judge and the classifier on the held-out injected texts, with the false positives apart.
"""
from lib import detector, report  # lib first: threads and seeds are fixed here


def main():
    verdict = detector.judge_verdicts("open-4b")
    print(f"unparsed replies: {sum(v is None for v in verdict.values())} of {len(verdict)}")
    flag = {key: value == "yes" for key, value in verdict.items()}  # unparsed is not a yes: not flagged
    # The recorder's IDs: carrier-CASE for injected texts, benign-RECORD for benign records.
    (dev_c, dev_b), (held_c, held_b) = detector.split_ids("dev"), detector.split_ids("held-out")
    report.rate_lines("dev true positives, injected texts flagged", [flag[k] for k in dev_c])
    report.rate_lines("dev false positives, benign records flagged", [flag[k] for k in dev_b])
    # Calibration: agreement with the labels on dev, where injected texts are labelled 1 and benign records 0.
    labelled = [(k, 1) for k in dev_c] + [(k, 0) for k in dev_b]
    report.rate_lines(f"dev agreement with labels, {len(labelled)} texts", [flag[k] == bool(y) for k, y in labelled])
    report.rate_lines("held-out true positives, injected texts flagged", [flag[k] for k in held_c])
    report.rate_lines("held-out false positives, benign records flagged", [flag[k] for k in held_b])
    assert not any(flag[k] for k in dev_b + held_b), "the judge flagged a benign record"  # the prose says it flagged none
    # Public corpora: deepset rows carry labels; gandalf rows are all attacks, so only recall is reported.
    deepset = [(f"public-deepset-prompt-injections-{r}", y) for r, _, y in detector.public_rows("deepset-prompt-injections")]
    report.rate_lines("deepset injection rows flagged", [flag[k] for k, y in deepset if y == 1])
    report.rate_lines("deepset benign rows flagged", [flag[k] for k, y in deepset if y == 0])
    gandalf = detector.public_rows("gandalf-ignore-instructions")
    report.rate_lines("gandalf attack rows flagged (recall only)",
                      [flag[f"public-gandalf-ignore-instructions-{r}"] for r, _, _ in gandalf])
    # The classifier on the held-out texts at the dev threshold, for the paired comparison with the judge.
    pick = detector.dev_threshold()
    classifier = detector.held_out_classifier(pick)
    # The gap is read on the injected texts only, as a true-positive-rate difference, and the false positives are paired
    # apart: the two rates answer different questions, so they are not pooled into one count.
    n = len(held_c)
    report.paired("held-out injected texts, true-positive rate, judge minus classifier", classifier[:n],
                  [flag[k] for k in held_c])
    report.paired("held-out benign records, false-positive rate, judge minus classifier", classifier[n:],
                  [flag[k] for k in held_b])
    print(f"held-out classifier flags: {sum(classifier[:n])} injected, {sum(classifier[n:])} benign")
    # The correction is computed in lib, with the chapter's 0.1 floor; the labelled share is printed beside it, to read
    # the correction against, since the set mixes injected and benign texts.
    c = detector.calibrate(flag, dev_c, dev_b, held_c, held_b)
    print(f"dev true positive rate, TPR: {c['tpr']:.3f}, {sum(flag[k] for k in dev_c)} of {len(dev_c)} injected")
    print(f"dev true negative rate, TNR: {c['tnr']:.3f}, {sum(not flag[k] for k in dev_b)} of {len(dev_b)} benign")
    print(f"denominator, TPR + TNR - 1: {c['denominator']:.3f} (the chapter refuses below 0.100)")
    print(f"held-out observed flag rate, {len(held_c) + len(held_b)} texts: {c['observed']:.3f}")
    print(f"held-out corrected share of injected texts: {c['corrected']:.3f}")
    print(f"held-out labelled share of injected texts, for reading the correction: {c['labelled_share']:.3f}")
    print(f"threshold, picked on dev: {pick:.2f}")


if __name__ == "__main__":
    main()
