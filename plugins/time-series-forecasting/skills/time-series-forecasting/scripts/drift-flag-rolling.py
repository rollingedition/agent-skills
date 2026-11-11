"""Flag drift against the backtest. The reference is the median daily MASE of the calibration days, Dec 9 to Dec 20, 2014,
which are earlier than the held-out week. A day is flagged when its MASE is above FLAG_FACTOR times that median. The
decision days, which are ordinary days, show how the flag behaves before the held-out week."""
from lib.electricity import load
from lib.panel import ALL30
from lib.running import (CAL_DAYS, DECISION_DAYS, FLAG_FACTOR, HELD_OUT_DAYS, daily_mase, flagged, prepare, run_days,
                         scale_from, with_actuals)
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
reference = daily_mase(with_actuals(run_days(df, CAL_DAYS), df), scale).median()
show("reference, median daily MASE", reference)
show("flag above, MASE", FLAG_FACTOR * reference)
decision = daily_mase(with_actuals(run_days(df, DECISION_DAYS), df), scale)
show("largest decision day, times the reference", decision.max() / reference)
show("decision days flagged", len(flagged(decision, reference)))
held = daily_mase(with_actuals(run_days(df, HELD_OUT_DAYS), df), scale)
for day, value in held.items():
    show(f"MASE {day:%Y-%m-%d}", value)
show("held-out days flagged", len(flagged(held, reference)))
show("flagged held-out days", ", ".join(f"{day:%Y-%m-%d}" for day in flagged(held, reference)))
