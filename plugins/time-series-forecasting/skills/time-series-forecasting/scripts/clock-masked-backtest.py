"""The Sunday backtest of 2014 for eight clients, scored twice: as the readings stand, and with the clock-change rule, which
leaves the masked hours out of the scores and fills the history. The prose's comparison rests on the masked-hour count,
the two pooled MAE lines, the two mean MASE lines and the two scored-hour lines."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import CLOCK_CHANGE_QUIRKS, filled_history, mask_clock_changes, seasonal_naive_at, year_scores
from lib.scoring import book_scale
from lib.settings import SUBSET8, show

cutoffs = pd.date_range("2014-01-05", "2014-12-28", freq="W-SUN")  # the same 52 Sunday cutoffs as the plain backtest
df = load(SUBSET8)[["unique_id", "ds", "y", "quirk"]]
masked = mask_clock_changes(df)  # a copy with the gap and repeat hours set to NaN; the rule's scores skip them
scale = book_scale(df, cutoffs[0])  # book_scale masks the clock-change hours itself, so both runs share this one scale

plain = seasonal_naive_at(df, cutoffs, lambda c: history_before(df, c))  # as the readings stand: the zeros and the doubled hour stay in
ruled = seasonal_naive_at(masked, cutoffs, lambda c: filled_history(masked, c))  # the rule: history filled from before each cutoff
show("masked hours in scored windows", int(plain["quirk"].isin(CLOCK_CHANGE_QUIRKS).sum()))  # counted in the plain run, where the flags are still present
for tag, scored in [("without the mask", plain), ("with the mask", ruled)]:
    result = year_scores(scored, scale)
    show(f"scored hours {tag}", result["scored hours"])
    show(f"MAE {tag}", result["MAE"])
    show(f"mean MASE {tag}", result["mean MASE"])
