"""Seasonal naive around the October clock change, for the subset of eight clients: the raw failure, then the rule."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import filled_history, mae_of, mask_clock_changes, median_client_ratio, seasonal_naive_at
from lib.settings import SUBSET8, show

cutoffs = pd.date_range("2014-10-19", "2014-11-02", freq="D")  # 15 daily cutoffs around Oct 26, 2014
next_day = pd.Timestamp("2014-10-27 01:00")
df = load(SUBSET8)[["unique_id", "ds", "y", "quirk"]]
masked = mask_clock_changes(df)

raw = seasonal_naive_at(df, cutoffs, lambda c: history_before(df, c))
repeat = raw["quirk"] == "clock_change_repeat"
at_next_day = raw["ds"] == next_day
show("repeat hours in actuals", int(repeat.sum()))
show("repeat-hour MAE with no rule", mae_of(raw[repeat]))
show("other-hour MAE with no rule", mae_of(raw[~repeat]))
show("median client ratio, repeat hour to other hours, no rule", median_client_ratio(raw, repeat, ~repeat))
show("next-day MAE at 1am with no rule", mae_of(raw[at_next_day]))
show("median client ratio, next-day 1am to other hours, no rule", median_client_ratio(raw, at_next_day, ~repeat))

no_fill = seasonal_naive_at(masked, cutoffs, lambda c: history_before(masked, c))
show("NaN forecasts without the fill", int(no_fill["SeasonalNaive"].isna().sum()))

fixed = seasonal_naive_at(masked, cutoffs, lambda c: filled_history(masked, c))
show("next-day MAE at 1am with the rule", mae_of(fixed[fixed["ds"] == next_day]))
show("other-hour MAE with the rule", mae_of(fixed[fixed["quirk"] != "clock_change_repeat"]))
