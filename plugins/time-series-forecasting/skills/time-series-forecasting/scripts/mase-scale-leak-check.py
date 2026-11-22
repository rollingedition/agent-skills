"""Score the lead client's held-out week in MASE with a scale from history and with one from the whole series, both with the clock-change readings masked. The point rests on the two last-reading lines, which show where each scale stops, and on the MASE ratio lines."""
import pandas as pd

from lib.backtest import held_out_cutoffs
from lib.baselines import BASELINES, baseline_forecasts, mase_scores, scale_history, seasonal_scale
from lib.electricity import load
from lib.quirks import mask_clock_changes
from lib.settings import HELD_OUT_WEEK, LEAD, show

LABELS = ["naive", "seasonal naive", "average of weeks"]    # printed names, in the order of BASELINES
first_day = pd.Timestamp(HELD_OUT_WEEK[0])                   # the first test day: the history scale may read only readings before it

full = load([LEAD])                                          # every reading of the lead client, with the quirk column that marks clock-change hours
df = full[["unique_id", "ds", "y"]]                          # the three columns the baselines and mase_scores read; quirk is for masking only
forecasts = baseline_forecasts(df, held_out_cutoffs())       # the same windows and history rule as naive-baselines-held-out-week.py
history = scale_history(full, first_day)                     # keeps only rows strictly before the first test day, so no test hour reaches this scale
masked_history = mask_clock_changes(history)                 # clock-change hours set to NaN, so the pairs that touch them drop out of the mean
masked_whole = mask_clock_changes(full)                      # the same masking on the whole series, so the test week is the only difference
test_rows = len(full[full["ds"] >= first_day])               # readings from the first test day on: the test week's rows

show("scale rows from history", len(history))
show("last scale reading from history", history["ds"].max().strftime("%b %d, %Y %H:%M"))   # this must be the hour before the first test day; the line is the check
show("scale rows from whole series", len(full))
show("last reading of whole series", full["ds"].max().strftime("%b %d, %Y %H:%M"))
show("test week share of whole-series rows in percent", 100 * test_rows / len(full), digits=3)
show("clock-change rows in scale history", int(history["quirk"].ne("normal").sum()))   # every quirk but normal; for the lead client these are the clock-change hours, as it has no late start
show("test week own mean day-to-day difference", seasonal_scale(full[full["ds"] >= first_day - pd.Timedelta(24, unit="h")]).loc[LEAD], digits=4)   # starts 24 hours early, so its first pair is the first test day against the day before
show("scale from history as recorded", seasonal_scale(history).loc[LEAD], digits=4)          # seasonal_scale returns one value per client, so .loc picks the lead client; the clock-change pairs are kept here
show("scale from history clock changes masked", seasonal_scale(masked_history).loc[LEAD], digits=4)   # pairs with a NaN are left out of the mean
show("scale from whole series clock changes masked", seasonal_scale(masked_whole).loc[LEAD], digits=4)

hist = mase_scores(df, forecasts, BASELINES, masked_history).loc[LEAD]   # the scale comes from the rows passed as train, not from df; that choice is what this example tests
whole = mase_scores(df, forecasts, BASELINES, masked_whole).loc[LEAD]
for model, label in zip(BASELINES, LABELS):
    show(f"{label} MASE from history scale", hist[model])
    show(f"{label} MASE from whole-series scale", whole[model])
    show(f"{label} MASE ratio whole-series over history", whole[model] / hist[model], digits=4)   # both MASEs share the same errors, so this ratio is the history scale over the whole-series scale
show("seasonal naive MASE from history scale at four decimals", hist["SeasonalNaive"], digits=4)   # two decimals hide the leak, so the last two lines print four
show("seasonal naive MASE from whole-series scale at four decimals", whole["SeasonalNaive"], digits=4)
