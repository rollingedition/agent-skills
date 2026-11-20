"""How much the corrected pass rate of corrected-pass-rate depends on its inputs. A 95% bootstrap interval resamples both the
dev calibration rows and the readable test items, with the book's fixed seed. It prints the share of resamples that reach
the 100% cap, and the corrected rate when one dev row moves TPR or TNR up or down. Only dev rows set the correction's rates."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from dataclasses import replace

from lib.calibration import confusion, correction_interval, corrected_pass_rate, helpsteer2_judgments, readable_verdicts, tnr, tpr
from lib.judging import passed
from lib.prompts import REF_SHA256
from lib.stats import RESAMPLES, interval_pct, pct
from lib.testset import load_items

items = load_items()  # all 120 items of the test set, as in corrected-pass-rate
found, _ = readable_verdicts("judge-answers-baseline", [item.id for item in items], REF_SHA256)
observed = int(passed(found).sum()) / len(found)

dev_rows = helpsteer2_judgments("dev")
dev = confusion(dev_rows)
lo, hi, capped, refused = correction_interval(dev_rows, passed(found))  # resamples the dev rows and the readable items
print(f"corrected pass rate, 95% interval: {interval_pct(lo, hi)}")
print(f"resamples at the 100% cap: {pct(capped, RESAMPLES)}")
print(f"resamples refused, TPR + TNR - 1 below 0.1: {pct(refused, RESAMPLES)}")

# One dev row moved: a human PASS row judged the other way changes TPR; a human FAIL row changes TNR.
moved = {
    "TPR one row higher": replace(dev, tp=dev.tp + 1, fn=dev.fn - 1),
    "TPR one row lower": replace(dev, tp=dev.tp - 1, fn=dev.fn + 1),
    "TNR one row higher": replace(dev, tn=dev.tn + 1, fp=dev.fp - 1),
    "TNR one row lower": replace(dev, tn=dev.tn - 1, fp=dev.fp + 1),
}
for label, counts in moved.items():
    print(f"corrected, {label}: {100 * corrected_pass_rate(observed, tpr(counts), tnr(counts)):.1f}%")
