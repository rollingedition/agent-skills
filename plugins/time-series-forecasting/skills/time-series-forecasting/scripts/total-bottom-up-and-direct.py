"""Forecast the total of the thirty clients two ways: bottom-up, the sum of the client forecasts, and direct, one model on
the total. Choose the method, and the direct model's target scaling, on the four decision windows by MAE on the total.
Then report both methods on the three standard cutoffs beside seasonal naive, on the total's MASE scale. The last lines
check the total against its parts and the scale against readings after each scored cutoff."""
import pandas as pd

from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours
from lib.scoring import actual_hours, score_windows
from lib.settings import EVAL_CUTOFFS, show
from lib.totals import (DIRECT_SCALED, METHODS, TOTAL, direct_windows, plain_mae, pooled_mae, total_checks,
                        total_forecasts, total_frame, total_scale_rows)

raw = load(ALL30)
total = total_frame(raw)
dec, cut = pd.to_datetime(DECISION_CUTOFFS), pd.to_datetime(EVAL_CUTOFFS)

dec_actual = actual_hours(total, dec)
dec_mae = pooled_mae(dec_actual, total_forecasts(raw, dec), ["bottom-up", "direct"])
direct_setting = {s: pooled_mae(dec_actual, direct_windows(raw, dec, scaled=s), ["direct"])["direct"]
                  for s in (True, False)}
if direct_setting[DIRECT_SCALED] != min(direct_setting.values()):
    raise ValueError("DIRECT_SCALED is not the target setting with the lower MAE on the decision windows")
show("decision cutoffs", len(dec))
show("decision holiday hours", check_decision_hours(dec_actual))
show("MAE bottom-up, decision windows", dec_mae["bottom-up"])
show("MAE direct, decision windows", dec_mae["direct"])
show("MAE direct with a scaled target, decision windows", direct_setting[True])
show("chosen direct target", "unscaled" if not DIRECT_SCALED else "scaled")
show("MAE bottom-up without identifier, decision windows", plain_mae(raw, dec))
show("chosen total method", dec_mae.idxmin())

scale = total_scale_rows(raw, cut[0])
scored, per_client = score_windows(actual_hours(total, cut), total_forecasts(raw, cut), METHODS, scale)
show("scored hours", len(scored))
show("MASE scale of the total", seasonal_scale(scale)[TOTAL])
for model in METHODS:
    show(f"MAE {model}", (scored["y"] - scored[model]).abs().mean())
for model in METHODS:
    show(f"MASE {model}", per_client.loc[TOTAL, model])
show("MAE bottom-up without identifier", plain_mae(raw, cut))
for label, value in total_checks(raw, cut[0], cut).items():
    show(label, value)
