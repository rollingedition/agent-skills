"""Qwen3Guard's verdicts on the same texts, replayed from its recording and parsed as its chat template defines them:
how many injected texts it labels unsafe or with any category, on dev and held-out, and how many benign records, beside
the classifier's flags on the same texts.

The point rests on the flagged-injected counts: the guard and the classifier flag different injected texts, so a
content-safety guard is not an injection detector.
"""
import re

from lib import detector, report  # lib first: threads and seeds are fixed here

# The two lines the chat template asks for: the label, then the categories, which read 'None' for safe text.
FORMAT = re.compile(r"Safety: (Safe|Unsafe|Controversial)\nCategories: ([^\n]*)")


def parse(raw):
    """(label, categories) from a reply in that format, or None when it is not in it."""
    found = FORMAT.fullmatch(raw.strip())
    return None if found is None else (found[1], [c.strip() for c in found[2].split(",") if c.strip() not in ("", "None")])


def main():
    verdict = {key: parse(raw) for key, raw in detector.recorded_verdicts("guard").items()}
    print(f"unparsed replies: {sum(v is None for v in verdict.values())} of {len(verdict)}")
    # An unparsed reply counts as neither unsafe nor a category. The guard flags a text it labels unsafe or categorises.
    unsafe = {k: v is not None and v[0] == "Unsafe" for k, v in verdict.items()}
    category = {k: v is not None and bool(v[1]) for k, v in verdict.items()}
    guard = {k: unsafe[k] or category[k] for k in verdict}
    (dev_c, dev_b), (held_c, held_b) = detector.split_ids("dev"), detector.split_ids("held-out")
    for name, keys in (("dev injected texts", dev_c), ("held-out injected texts", held_c),
                       ("dev benign records", dev_b), ("held-out benign records", held_b)):
        report.rate_lines(f"{name}, labelled unsafe", [unsafe[k] for k in keys])
        report.rate_lines(f"{name}, with any category", [category[k] for k in keys])
    # The classifier at the dev threshold, on the same injected texts, beside the guard's flags on them.
    pick = detector.dev_threshold()
    injected = dev_c + held_c
    texts = [t for s in ("dev", "held-out") for _, t in detector.attack_carriers(s)]
    classifier = [s >= pick for s in detector.score(texts)]
    flagged = [guard[k] for k in injected]
    report.rate_lines("injected texts flagged by the classifier, dev and held-out", classifier)
    report.rate_lines("injected texts flagged by the guard, dev and held-out", flagged)
    report.paired("guard minus classifier, injected texts flagged", classifier, flagged)
    both = sum(c and g for c, g in zip(classifier, flagged))
    print(f"flagged by both: {both}")
    print(f"flagged by the guard only: {sum(flagged) - both}")
    print(f"flagged by the classifier only: {sum(classifier) - both}")
    # The guard flags fewer injected texts than the classifier does: a yes or no the prose relies on.
    assert sum(flagged) < sum(classifier), "the guard flags as many injected texts as the classifier"
    benign = dev_b + held_b
    report.rate_lines(f"benign records flagged by the guard, {len(benign)}", [guard[k] for k in benign])


if __name__ == "__main__":
    main()
