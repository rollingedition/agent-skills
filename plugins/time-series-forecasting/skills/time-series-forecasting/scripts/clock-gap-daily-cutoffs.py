"""Seasonal naive around the March clock change, for the subset of eight clients: the raw failure, then the rule."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import filled_history, mae_of, mask_clock_changes, median_client_ratio, seasonal_naive_at
from lib.settings import SUBSET8, show

cutoffs = pd.date_range("2014-03-23", "2014-04-06", freq="D")  # 15 daily cutoffs around Mar 30, 2014
next_day = pd.Timestamp("2014-03-31 01:00")
df = load(SUBSET8)[["unique_id", "ds", "y", "quirk"]]
masked = mask_clock_changes(df)

raw = seasonal_naive_at(df, cutoffs, lambda c: history_before(df, c))
gap = raw["quirk"] == "clock_change_gap"
at_next_day = raw["ds"] == next_day
show("gap hours in actuals", int(gap.sum()))
show("gap hours that read zero", int((raw[gap]["y"] == 0).sum()))
show("gap-hour MAE with no rule", mae_of(raw[gap]))
show("other-hour MAE with no rule", mae_of(raw[~gap]))
show("median client ratio, gap hour to other hours, no rule", median_client_ratio(raw, gap, ~gap))
show("next-day MAE at 1am with no rule", mae_of(raw[at_next_day]))
show("next-day 1am forecasts that are zero, no rule", int((raw[at_next_day]["SeasonalNaive"] == 0).sum()))
show("median client ratio, next-day 1am to other hours, no rule", median_client_ratio(raw, at_next_day, ~gap))

no_fill = seasonal_naive_at(masked, cutoffs, lambda c: history_before(masked, c))
show("NaN forecasts without the fill", int(no_fill["SeasonalNaive"].isna().sum()))

fixed = seasonal_naive_at(masked, cutoffs, lambda c: filled_history(masked, c))
show("next-day MAE at 1am with the rule", mae_of(fixed[fixed["ds"] == next_day]))
show("other-hour MAE with the rule", mae_of(fixed[fixed["quirk"] != "clock_change_gap"]))
