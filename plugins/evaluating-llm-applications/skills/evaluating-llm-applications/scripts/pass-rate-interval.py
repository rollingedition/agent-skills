"""The baseline's pass rate over the twenty chapter items, judged by the reference-guided judge, with its 95% interval.

Every item is in the denominator, and a correct decline counts as a pass. The interval resamples items."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import chapter_items
from lib.judging import passed, verdicts
from lib.stats import bootstrap_mean, interval_pct, pct

items = chapter_items()
found = verdicts("judge-answers-baseline", [item.id for item in items])  # keyed in sorted id order
scores = passed(found)  # 1.0 for PASS, 0.0 for FAIL, in the same order
print(f"items: {len(items)}")
print(f"pass rate: {pct(int(scores.sum()), len(items))}")
lo, hi = bootstrap_mean(scores)  # level 0.95 for one comparison; seed SEED, 2,000 resamples
print(f"95% interval of the pass rate: {interval_pct(lo, hi)}")

kind_of = {item.id: item.kind for item in items}
for kind in ("answerable", "unanswerable", "version-dependent", "ambiguous"):
    ids = [item_id for item_id in found if kind_of[item_id] == kind]
    passes = sum(1 for item_id in ids if found[item_id] == "PASS")
    print(f"pass rate, {kind}: {pct(passes, len(ids))}")
