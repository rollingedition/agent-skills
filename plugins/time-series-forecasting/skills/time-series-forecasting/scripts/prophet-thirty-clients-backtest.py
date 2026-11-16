"""Prophet for each of the thirty clients on the three standard cutoffs, with a 95% interval, scored on the book's MASE
scale beside seasonal naive and the Chapter 6 global model. The point that Prophet's mean MASE is higher rests on
the mean MASE lines, and the coverage line says whether its 95% interval holds."""
import pandas as pd

from lib.compare import (PROPHET_HOLIDAYS, PROPHET_LEVEL, global_forecasts, prophet_windows, report_range,
                         report_subset, score, seasonal_naive)
from lib.electricity import load
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import report_scores
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
# clock-change hours set to missing, as chapter 3 sets them
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = pd.DatetimeIndex(EVAL_CUTOFFS)
# Prophet at the book's settings from lib.compare: holiday table off, 95% interval, one fit per client and cutoff
forecasts = prophet_windows(df, cutoffs).merge(
    seasonal_naive(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one").merge(
    global_forecasts(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one")
models = ["Prophet", "SeasonalNaive", "Global"]
# per_client: one MASE per client and model; scored: forecasts beside readings
per_client, scored = score(raw, forecasts, models, ALL30)

show("Prophet interval level", PROPHET_LEVEL)
show("Prophet holiday table", "on" if PROPHET_HOLIDAYS else "off")
show("clients scored", scored["unique_id"].nunique())
show("scored hours", len(scored))
show("clients where Prophet beats seasonal naive", int((per_client["Prophet"] < per_client["SeasonalNaive"]).sum()))
show("clients where Prophet beats the global model", int((per_client["Prophet"] < per_client["Global"]).sum()))
report_scores(scored, per_client, models)
report_subset(per_client, models)
# the 95% range from Prophet's lower and upper interval columns
report_range(scored, "Prophet", "ProphetLo", "ProphetHi", PROPHET_LEVEL)
# Sensitivity only, not used to choose: the holiday table on the same cutoffs, which the decision windows
# did not favour.
# two processes; each fit is the same at any worker count
on = prophet_windows(df, cutoffs, use_holidays=True, workers=2)[["unique_id", "ds", "Prophet"]].rename(
    columns={"Prophet": "ProphetHolidays"})
per_holiday, _ = score(raw, forecasts.merge(on, on=["unique_id", "ds"], validate="one_to_one"),
                       ["ProphetHolidays"], ALL30)
show("mean MASE Prophet with holidays, not chosen", per_holiday["ProphetHolidays"].mean())
