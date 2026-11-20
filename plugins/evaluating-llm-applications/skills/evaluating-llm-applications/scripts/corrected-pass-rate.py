"""The baseline's answer-judge pass rate over the test items the judge gave a readable verdict, corrected for the judge's errors
with TPR and TNR from dev only. The corrected rate is printed beside the observed rate and the two rates the correction uses.

One judge reply has no PASS or FAIL on its first line. It is left out of the rate and printed by name, never counted as a
FAIL. The TPR and TNR come from HelpSteer2, where the judge rates other models' answers without a reference. This judge reads
the answers against a written reference. The correction assumes the two error profiles transfer; nothing here tests that.
The last lines apply the same correction to the calibration set itself: the rates are measured on those same rows, so that
check shows the arithmetic, not how well the correction generalises."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import (
    confusion,
    corrected_pass_rate,
    crossover_pass_rate,
    helpsteer2_judgments,
    readable_verdicts,
    tnr,
    tpr,
)
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import pct
from lib.testset import load_items

items = load_items()  # all 120 items of the test set, dev and held-out together
found, unreadable = readable_verdicts("judge-answers-baseline", [item.id for item in items], REF_SHA256)
details = "".join(f' ({item_id}, "{first}")' for item_id, first in unreadable)
print(f"unreadable verdicts: {len(unreadable)}{details}")  # left out of the rate below, not counted as FAIL
passes = int(passed(found).sum())  # found is keyed in sorted id order
observed = passes / len(found)
print(f"observed pass rate, readable items: {pct(passes, len(found))}")

dev = confusion(helpsteer2_judgments("dev"))  # the only rows the correction's TPR and TNR may come from
print(f"TPR, dev: {pct(dev.tp, dev.tp + dev.fn)}")
print(f"TNR, dev: {pct(dev.tn, dev.tn + dev.fp)}")
# Below this observed rate the correction lowers the rate; above it, the correction raises it.
crossover = crossover_pass_rate(tpr(dev), tnr(dev))
print(f"crossover point, dev: {100 * crossover:.1f}% (TPR {100 * tpr(dev):.1f}%, TNR {100 * tnr(dev):.1f}%)")

corrected = corrected_pass_rate(observed, tpr(dev), tnr(dev))  # refused if TPR + TNR - 1 is below 0.1
print(f"corrected pass rate: {100 * corrected:.1f}%")

# The sanity check: the same correction on the calibration set, with rates measured on those same rows. It checks the
# arithmetic, not transfer to the answers: it should return the human PASS rate, and it does by construction.
calibration = confusion(helpsteer2_judgments())
judge_rate = (calibration.tp + calibration.fp) / calibration.n
print(f"calibration set, judge PASS rate: {pct(calibration.tp + calibration.fp, calibration.n)}")
print(f"calibration set, corrected judge PASS rate: {100 * corrected_pass_rate(judge_rate, tpr(calibration), tnr(calibration)):.1f}%")
print(f"calibration set, human PASS rate: {pct(calibration.tp + calibration.fn, calibration.n)}")
calibration_crossover = crossover_pass_rate(tpr(calibration), tnr(calibration))  # the same test, on the same rows
print(f"crossover point, calibration set: {100 * calibration_crossover:.1f}% "
      f"(TPR {100 * tpr(calibration):.1f}%, TNR {100 * tnr(calibration):.1f}%)")
