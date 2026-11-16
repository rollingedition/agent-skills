"""Seasonal naive around the March clock change, for eight clients: the raw failure, then the rule. The prose's claims rest
on the gap-hour and next-day 1am lines, with and without the rule, the median client ratios, and the count of missing
forecasts without the fill."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import filled_history, mae_of, mask_clock_changes, median_client_ratio, seasonal_naive_at
from lib.settings import SUBSET8, show

cutoffs = pd.date_range("2014-03-23", "2014-04-06", freq="D")  # 15 daily cutoffs around Mar 30, 2014
next_day = pd.Timestamp("2014-03-31 01:00")  # 01:00 the day after the change: the forecast that copies the zero
df = load(SUBSET8)[["unique_id", "ds", "y", "quirk"]]
masked = mask_clock_changes(df)  # a copy with the gap and repeat hours set to NaN

raw = seasonal_naive_at(df, cutoffs, lambda c: history_before(df, c))  # no rule: the history keeps the zeros as the file has them
gap = raw["quirk"] == "clock_change_gap"  # the file's flag marks the gap hours
at_next_day = raw["ds"] == next_day
show("gap hours in actuals", int(gap.sum()))
show("gap hours that read zero", int((raw[gap]["y"] == 0).sum()))
show("gap-hour MAE with no rule", mae_of(raw[gap]))
show("other-hour MAE with no rule", mae_of(raw[~gap]))
# per client: the mean error at gap hours over the mean at other hours, then the median across clients
show("median client ratio, gap hour to other hours, no rule", median_client_ratio(raw, gap, ~gap))
show("next-day MAE at 1am with no rule", mae_of(raw[at_next_day]))
# a forecast of exactly zero is the March zero copied forward from the day before
show("next-day 1am forecasts that are zero, no rule", int((raw[at_next_day]["SeasonalNaive"] == 0).sum()))
show("median client ratio, next-day 1am to other hours, no rule", median_client_ratio(raw, at_next_day, ~gap))

no_fill = seasonal_naive_at(masked, cutoffs, lambda c: history_before(masked, c))  # masked history, no fill: a NaN copies forward and stays NaN
show("NaN forecasts without the fill", int(no_fill["SeasonalNaive"].isna().sum()))

fixed = seasonal_naive_at(masked, cutoffs, lambda c: filled_history(masked, c))  # the rule: masked hours filled from the history before each cutoff
show("next-day MAE at 1am with the rule", mae_of(fixed[fixed["ds"] == next_day]))
show("other-hour MAE with the rule", mae_of(fixed[fixed["quirk"] != "clock_change_gap"]))
