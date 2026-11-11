"""Score the recorded Chronos-2 forecasts on the same three standard cutoffs and MASE scale as the other models. The median
is the point forecast. The 80% range runs from the 0.1 to the 0.9 quantile, and the 95% range from 0.025 to 0.975.
The code reads the recording only; it never calls the model."""
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
forecasts = recorded_forecasts().merge(
    seasonal_naive(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one").merge(
    global_forecasts(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one")
models = ["Chronos", "SeasonalNaive", "Global"]
per_client, scored = score(raw, forecasts, models, ALL30)

show("clients scored", scored["unique_id"].nunique())
show("scored hours", len(scored))
show("clients where Chronos beats seasonal naive", int((per_client["Chronos"] < per_client["SeasonalNaive"]).sum()))
report_scores(scored, per_client, models)
report_subset(per_client, models)
report_pinball(scored, "Chronos", "q10", 0.1)
report_pinball(scored, "Chronos", "q50", 0.5)
report_pinball(scored, "Chronos", "q90", 0.9)
report_range(scored, "Chronos", "q10", "q90", 80)
report_range(scored, "Chronos", "q025", "q975", 95)
