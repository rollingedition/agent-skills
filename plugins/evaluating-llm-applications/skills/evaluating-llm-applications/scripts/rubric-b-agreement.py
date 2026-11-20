"""How often the second rubric's verdicts agree with the human ratings on the HelpSteer2 sample, beside the first rubric's,
on dev and on held-out, with kappa, TPR and TNR and the PASS rates of judge and humans.

The second rubric was recorded on dev only, so its held-out line says so instead of printing a rate. The paired difference
is on dev alone: each dev row's agreement under rubric B minus its agreement under rubric A, bootstrapped over rows. A
reply with no readable verdict is printed by row ID and left out; it is never counted as FAIL."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from dataclasses import replace

from lib.calibration import cohens_kappa, confusion, helpsteer2_judgments, readable_verdicts
from lib.prompts import HS2B_SHA256
from lib.replay import ReplayModel
from lib.stats import bootstrap_mean, interval_points, pct

RUBRIC_B = "judge-helpsteer2-rubric-b"


def report(name, split, judgments):
    c = confusion(judgments)
    print(f"agreement, {name}, {split}: {pct(c.tp + c.tn, c.n)}")
    print(f"kappa, {name}, {split}: {cohens_kappa(c):.2f}")
    print(f"TPR, {name}, {split}: {pct(c.tp, c.tp + c.fn)}")
    print(f"TNR, {name}, {split}: {pct(c.tn, c.tn + c.fp)}")
    print(f"judge PASS rate, {name}, {split}: {pct(c.tp + c.fp, c.n)}")
    print(f"human PASS rate, {name}, {split}: {pct(c.tp + c.fn, c.n)}")


def same(j):
    return int(j.judge_pass == j.human_pass)


base = {j.id: j for j in helpsteer2_judgments()}  # rubric A's verdicts and the human PASS for every row, by id
recorded = {item for item, _ in ReplayModel(RUBRIC_B, HS2B_SHA256).keys()}
verdicts_b, unreadable = readable_verdicts(RUBRIC_B, sorted(recorded & base.keys()), HS2B_SHA256)
rows_b = {i: replace(base[i], judge_pass=v == "PASS") for i, v in verdicts_b.items()}

print(f"unreadable, rubric B: {len(unreadable)} of {len(recorded)} replies")
for item_id, _ in unreadable:
    print(f"unreadable, rubric B, row {item_id}: excluded, not counted as FAIL")
for split in ("dev", "held-out"):
    report("rubric A", split, [j for j in base.values() if j.split == split])
    b = [j for j in rows_b.values() if j.split == split]
    if b:
        report("rubric B", split, b)
    else:
        print(f"rubric B, {split}: no readable replies recorded")

dev_ids = [i for i in verdicts_b if base[i].split == "dev"]
diffs = [same(rows_b[i]) - same(base[i]) for i in dev_ids]  # the same row under both rubrics
lo, hi = bootstrap_mean(diffs)  # level 0.95 for one comparison; seed SEED, 2,000 resamples
n = len(dev_ids)
print(f"paired difference, dev: {100 * sum(diffs) / n:+.1f} points, 95% interval {interval_points(lo, hi)}, n = {n}")
reading = "rubric B better" if lo > 0 else "rubric B worse" if hi < 0 else f"no difference detected at n = {n}"
caveat = ", on dev only with no held-out run" if lo > 0 or hi < 0 else ""  # a dev-only difference carries its caveat
print(f"paired difference, dev, reading: {reading}{caveat}")
