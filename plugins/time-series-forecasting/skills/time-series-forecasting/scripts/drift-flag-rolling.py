"""Flags drift against the backtest: a day is flagged when its daily MASE is above FLAG_FACTOR times the reference, the
median daily MASE of the calibration days, Dec 9 to Dec 20, 2014, which are earlier than the held-out week. The
`largest decision day` and `decision days flagged` lines show the ordinary days staying under the line, and the `MASE`
and `held-out days flagged` lines show which held-out days cross it."""
from lib.electricity import load
from lib.panel import ALL30
from lib.running import (CAL_DAYS, DECISION_DAYS, FLAG_FACTOR, HELD_OUT_DAYS, daily_mase, flagged, prepare, run_days,
                         scale_from, with_actuals)
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
reference = daily_mase(with_actuals(run_days(df, CAL_DAYS), df), scale).median()  # the median, not the mean, so one unusual calibration day moves it little
show("reference, median daily MASE", reference)
show("flag above, MASE", FLAG_FACTOR * reference)  # FLAG_FACTOR is 2, the chapter's rule of thumb
decision = daily_mase(with_actuals(run_days(df, DECISION_DAYS), df), scale)
show("largest decision day, times the reference", decision.max() / reference)
show("decision days flagged", len(flagged(decision, reference)))
held = daily_mase(with_actuals(run_days(df, HELD_OUT_DAYS), df), scale)
for day, value in held.items():
    show(f"MASE {day:%Y-%m-%d}", value)
show("held-out days flagged", len(flagged(held, reference)))
show("flagged held-out days", ", ".join(f"{day:%Y-%m-%d}" for day in flagged(held, reference)))
