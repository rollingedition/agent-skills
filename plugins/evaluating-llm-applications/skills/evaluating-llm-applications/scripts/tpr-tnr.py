"""The judge's true positive rate and true negative rate on the HelpSteer2 sample, with the counts beside each, on dev, on
held-out and on both together.

PASS is the positive class: TPR is the share of human PASS rows the judge passes, and TNR the share of human FAIL rows it
fails. The two rates are the judge's error profile; a lenient judge has a high TPR and a low TNR."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import confusion, helpsteer2_judgments
from lib.stats import pct

# PASS is the positive class: the rows a human rated PASS are the positives, and TPR is taken over them.
print("positive class: PASS")
for label, split in (("all", None), ("dev", "dev"), ("held-out", "held-out")):
    counts = confusion(helpsteer2_judgments(split))
    print(f"TPR, {label}: {pct(counts.tp, counts.tp + counts.fn)}")
    print(f"TNR, {label}: {pct(counts.tn, counts.tn + counts.fp)}")
