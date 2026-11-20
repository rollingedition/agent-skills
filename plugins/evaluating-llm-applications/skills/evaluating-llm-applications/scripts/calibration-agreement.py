"""How often the reference-free correctness judge agrees with the human ratings on the HelpSteer2 sample, and Cohen's kappa
for the same counts, on dev, on held-out and on both together.

Agreement alone reads higher than the judge's skill when most rows are one verdict, so the kappa line is the one to read
against chance: the chance agreement printed beside it is what the judge would reach by guessing at its own PASS rate."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.calibration import agreement, chance_agreement, cohens_kappa, confusion, helpsteer2_judgments
from lib.stats import pct

for label, split in (("all", None), ("dev", "dev"), ("held-out", "held-out")):
    counts = confusion(helpsteer2_judgments(split))
    print(f"agreement, {label}: {pct(counts.tp + counts.tn, counts.n)}")
    # the chance figure is an expected rate, not a count, so it has no denominator beside it
    print(f"chance agreement, {label}: {100 * chance_agreement(counts):.1f}%")
    # kappa is printed with two decimals (plan section 6.5), not as a percentage
    print(f"kappa, {label}: {cohens_kappa(counts):.2f}")
