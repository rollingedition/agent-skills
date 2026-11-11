"""Choose how a late reading is filled, on the decision windows, Nov 25 to Dec 3, 2014. For each decision cutoff, the lead
client's last six readings of the day before arrive at 09:00 on the cutoff day, as the Dec 28 readings do in the held-out
week. The forecast for that day fills them in one of two ways: forward from the last reading that arrived, or with the
reading of the same hour a week earlier. Only the lead client's hours 18:00 to 23:00 change, because lag 24 reads them.
The held-out week is not used."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import DECISION_DAYS, LATE_CLIENT, feed, late_copy, prepare, run_days, with_actuals
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
show("readings late for each decision cutoff", feed(late_copy(df, DECISION_DAYS[0]), DECISION_DAYS[0])[2])
errors = {}
for rule in ("forward", "week"):
    parts = []
    for day in DECISION_DAYS:
        scored = with_actuals(run_days(late_copy(df, day), [day], fill=rule), df)
        parts.append(scored.loc[(scored["unique_id"] == LATE_CLIENT) & (scored["hour"] >= 18), "ae"])
    errors[rule] = pd.concat(parts).mean()
    show(f"hours scored, {rule} fill", len(pd.concat(parts)))
    show(f"MAE, lead client hours 18 to 23, {rule} fill", errors[rule])
show("chosen late fill", min(errors, key=errors.get))
