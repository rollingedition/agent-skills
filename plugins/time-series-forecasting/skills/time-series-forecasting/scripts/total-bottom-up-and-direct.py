"""Forecasts the total of the thirty clients two ways, bottom-up (the sum of the client forecasts) and direct (one model on the
total), and chooses between them on the four decision windows by MAE on the total. The choice rests on the two decision-window
MAE lines; the standard cutoffs then report both beside seasonal naive, and the last two lines check the total and the scale."""
import pandas as pd

from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours
from lib.scoring import actual_hours, score_windows
from lib.settings import EVAL_CUTOFFS, show
from lib.totals import (DIRECT_SCALED, METHODS, TOTAL, direct_windows, plain_mae, pooled_mae, total_checks,
                        total_forecasts, total_frame, total_scale_rows)

raw = load(ALL30)
total = total_frame(raw)  # the hourly sum of the thirty clients, after the start rule; missing in a clock-change hour
dec, cut = pd.to_datetime(DECISION_CUTOFFS), pd.to_datetime(EVAL_CUTOFFS)

dec_actual = actual_hours(total, dec)
# the direct model here uses the target setting the book chose: DIRECT_SCALED is False, so the direct total is unscaled
dec_mae = pooled_mae(dec_actual, total_forecasts(raw, dec), ["bottom-up", "direct"])
# the direct model's MAE with its target scaled (True) and unscaled (False)
direct_setting = {s: pooled_mae(dec_actual, direct_windows(raw, dec, scaled=s), ["direct"])["direct"]
                  for s in (True, False)}
# stops the run if the constant no longer names the setting with the lower MAE
if direct_setting[DIRECT_SCALED] != min(direct_setting.values()):
    raise ValueError("DIRECT_SCALED is not the target setting with the lower MAE on the decision windows")
show("decision cutoffs", len(dec))
# raises if a decision hour is a Portuguese holiday or reaches the held-out week; the count is printed for the record
show("decision holiday hours", check_decision_hours(dec_actual))
show("MAE bottom-up, decision windows", dec_mae["bottom-up"])
show("MAE direct, decision windows", dec_mae["direct"])
show("MAE direct with a scaled target, decision windows", direct_setting[True])
show("chosen direct target", "unscaled" if not DIRECT_SCALED else "scaled")
# the bottom-up total without the client identifier, which Chapter 6 also tried
show("MAE bottom-up without identifier, decision windows", plain_mae(raw, dec))
show("chosen total method", dec_mae.idxmin())

# the scale reads the readings before the first standard cutoff, and no later ones
scale = total_scale_rows(raw, cut[0])
scored, per_client = score_windows(actual_hours(total, cut), total_forecasts(raw, cut), METHODS, scale)
show("scored hours", len(scored))
# seasonal_scale returns one value per unique_id, so [TOTAL] picks the total's
show("MASE scale of the total", seasonal_scale(scale)[TOTAL])
for model in METHODS:
    show(f"MAE {model}", (scored["y"] - scored[model]).abs().mean())
for model in METHODS:
    show(f"MASE {model}", per_client.loc[TOTAL, model])
show("MAE bottom-up without identifier", plain_mae(raw, cut))
# the first cutoff is passed as first_cutoff; the scale check then runs on every cutoff in cut
for label, value in total_checks(raw, cut[0], cut).items():
    show(label, value)
