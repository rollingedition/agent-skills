"""Score the recorded NHITS forecasts on the same three cutoffs and MASE scale as Chronos-2 and the other models. The
median is the point forecast. The 80% range runs from the 0.1 to the 0.9 quantile, and the 95% range from 0.025 to
0.975. Each level is trained directly by MQLoss, so no range is interpolated. The code reads the recording only."""
import pandas as pd

from lib.compare import (global_forecasts, recorded_forecasts, report_pinball, report_range, report_subset, score,
                         seasonal_naive)
from lib.electricity import load
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import report_scores
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = pd.DatetimeIndex(EVAL_CUTOFFS)
forecasts = recorded_forecasts("nhits", "NHITS").merge(
    seasonal_naive(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one").merge(
    global_forecasts(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one")
models = ["NHITS", "SeasonalNaive", "Global"]
per_client, scored = score(raw, forecasts, models, ALL30)

show("clients scored", scored["unique_id"].nunique())
show("scored hours", len(scored))
show("clients where NHITS beats seasonal naive", int((per_client["NHITS"] < per_client["SeasonalNaive"]).sum()))
report_scores(scored, per_client, models)
report_subset(per_client, models)
report_pinball(scored, "NHITS", "q10", 0.1)
report_pinball(scored, "NHITS", "q50", 0.5)
report_pinball(scored, "NHITS", "q90", 0.9)
report_range(scored, "NHITS", "q10", "q90", 80)
report_range(scored, "NHITS", "q025", "q975", 95)
