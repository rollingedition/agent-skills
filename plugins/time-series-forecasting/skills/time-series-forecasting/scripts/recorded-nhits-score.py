"""Scores the recorded NHITS forecasts on the same three cutoffs and MASE scale as Chronos-2 and the other models: the
median is the point forecast, and each range comes from levels trained directly, so none is interpolated. The point
about its ranges rests on the coverage and interval score lines, and the code reads the recording only, never the
model."""
import pandas as pd

from lib.compare import (global_forecasts, recorded_forecasts, report_pinball, report_range, report_subset, score,
                         seasonal_naive)
from lib.electricity import load
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import report_scores
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
# clock-change hours set to missing, as chapter 3 sets them
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = pd.DatetimeIndex(EVAL_CUTOFFS)
# the NHITS recording, read only after each output matches its manifest hash; its median is the NHITS column
forecasts = recorded_forecasts("nhits", "NHITS").merge(
    seasonal_naive(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one").merge(
    global_forecasts(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one")
models = ["NHITS", "SeasonalNaive", "Global"]
# per_client: one MASE per client and model; scored: forecasts beside readings
per_client, scored = score(raw, forecasts, models, ALL30)

show("clients scored", scored["unique_id"].nunique())
show("scored hours", len(scored))
show("clients where NHITS beats seasonal naive", int((per_client["NHITS"] < per_client["SeasonalNaive"]).sum()))
report_scores(scored, per_client, models)
report_subset(per_client, models)
report_pinball(scored, "NHITS", "q10", 0.1)                         # quantile loss at tau 0.1: the 0.1 quantile column
report_pinball(scored, "NHITS", "q50", 0.5)                         # at tau 0.5 the loss is half the absolute error
report_pinball(scored, "NHITS", "q90", 0.9)
report_range(scored, "NHITS", "q10", "q90", 80)
report_range(scored, "NHITS", "q025", "q975", 95)
