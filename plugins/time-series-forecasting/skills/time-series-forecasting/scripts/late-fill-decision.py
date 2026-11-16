"""Chooses how a late reading is filled on the decision windows, Nov 25 to Dec 3, 2014: the lead client's last six readings
of the day before arrive at 09:00 on each cutoff day, as the Dec 28 readings do in the held-out week. The
`MAE, lead client hours 18 to 23` lines decide between forward fill and a fill from the same hour a week earlier; only
those hours change, because lag 24 reads them, and the held-out week is not used."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import DECISION_DAYS, LATE_CLIENT, feed, late_copy, prepare, run_days, with_actuals
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
# feed returns (train, known, pending count, read_by); [2] is the pending count
show("readings late for each decision cutoff", feed(late_copy(df, DECISION_DAYS[0]), DECISION_DAYS[0])[2])
errors = {}
for rule in ("forward", "week"):
    parts = []
    for day in DECISION_DAYS:
        # the day before's last six readings arrive at 09:00 on this day, after its cutoff, so the fill applies
        scored = with_actuals(run_days(late_copy(df, day), [day], fill=rule), df)
        # 18:00 to 23:00 of the day scored, which lag 24 reads from the day before
        parts.append(scored.loc[(scored["unique_id"] == LATE_CLIENT) & (scored["hour"] >= 18), "ae"])
    errors[rule] = pd.concat(parts).mean()
    show(f"hours scored, {rule} fill", len(pd.concat(parts)))
    show(f"MAE, lead client hours 18 to 23, {rule} fill", errors[rule])
show("chosen late fill", min(errors, key=errors.get))
