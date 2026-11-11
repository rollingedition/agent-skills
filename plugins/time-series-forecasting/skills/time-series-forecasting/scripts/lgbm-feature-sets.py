"""Choose the feature set of a global LightGBM forecast of SUBSET8 on the decision windows (B-5, B-9, B-10): four ordinary
cutoffs and seven 2014 holidays before Dec 25. Each set is fitted scaled and unscaled. The standard cutoffs are reported
after the choice, and they choose nothing."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.features import CALENDAR, PT_HOLIDAYS, is_holiday, rows_reading_missing, score_feature_sets
from lib.panel import DECISION_CUTOFFS, HOLIDAY_DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, LEAD, SUBSET8, show

LAGS = [24, 168]
FEATURE_SETS = {"lags_only": [], "with_calendar": CALENDAR, "with_holidays": CALENDAR + [is_holiday]}
MODELS = ["SeasonalNaive", *FEATURE_SETS, *[f"unscaled_{name}" for name in FEATURE_SETS]]
DECISION = sorted([*DECISION_CUTOFFS, *HOLIDAY_DECISION_CUTOFFS])
raw = load(SUBSET8)

forecasts, scored, per_client = score_feature_sets(raw, DECISION, LAGS, FEATURE_SETS, DECISION[0])
show("clients", forecasts["unique_id"].nunique())
show("decision windows", len(DECISION))
show("scored hours", len(scored))
show("Portuguese holidays in 2013 and 2014", len(PT_HOLIDAYS))
show("holiday hours in the decision windows", int(is_holiday(scored["ds"]).sum()))
for model in MODELS:
    show(f"MAE {model.replace('unscaled_', 'unscaled ')}", (scored["y"] - scored[model]).abs().mean())
for model in MODELS:
    show(f"mean MASE {model.replace('unscaled_', 'unscaled ')}", per_client[model].mean(), digits=3)
for model in MODELS:
    show(f"MASE MT_268 {model.replace('unscaled_', 'unscaled ')}", per_client.loc["MT_268", model], digits=3)

# The standard cutoffs, reported beside the choice above. Nothing is chosen from them.
_, _, standard = score_feature_sets(raw, EVAL_CUTOFFS, LAGS, FEATURE_SETS, EVAL_CUTOFFS[0])
for model in MODELS:
    show(f"standard cutoffs, mean MASE {model.replace('unscaled_', 'unscaled ')}", standard[model].mean(), digits=3)

# Clock-change check: the history of a 1 April 2014 cutoff holds the 30 March gap, which the feature rules must reach.
march = history_before(mask_clock_changes(load([LEAD])), pd.Timestamp("2014-04-01"))
show("masked hours in the history", int(march["y"].isna().sum()))
show("rows whose lag reads a masked hour", rows_reading_missing(march.set_index("ds")["y"], LAGS))
