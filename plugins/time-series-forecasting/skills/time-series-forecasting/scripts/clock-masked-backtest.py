"""The Sunday backtest of 2014 with the clock-change rule: masked hours left out of the scores, history filled."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import CLOCK_CHANGE_QUIRKS, filled_history, mask_clock_changes, seasonal_naive_at, year_scores
from lib.scoring import book_scale
from lib.settings import SUBSET8, show

cutoffs = pd.date_range("2014-01-05", "2014-12-28", freq="W-SUN")  # the same 52 Sunday cutoffs as the plain backtest
df = load(SUBSET8)[["unique_id", "ds", "y", "quirk"]]
masked = mask_clock_changes(df)
scale = book_scale(df, cutoffs[0])

plain = seasonal_naive_at(df, cutoffs, lambda c: history_before(df, c))
ruled = seasonal_naive_at(masked, cutoffs, lambda c: filled_history(masked, c))
show("masked hours in scored windows", int(plain["quirk"].isin(CLOCK_CHANGE_QUIRKS).sum()))
for tag, scored in [("without the mask", plain), ("with the mask", ruled)]:
    result = year_scores(scored, scale)
    show(f"scored hours {tag}", result["scored hours"])
    show(f"MAE {tag}", result["MAE"])
    show(f"mean MASE {tag}", result["mean MASE"])
