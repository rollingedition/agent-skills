"""Prophet with and without the Portuguese holiday table, on the eleven decision windows for SUBSET8 (B-9, B-10),
before any standard cutoff is scored. The point that the table stays off rests on the two mean MASE lines and on
holiday table kept, which says whether the table lowers the mean per-client MASE."""
from lib.compare import prophet_windows, seasonal_naive, score
from lib.electricity import load
from lib.features import is_holiday
from lib.panel import DECISION_CUTOFFS, HOLIDAY_DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.settings import SUBSET8, show

# the four ordinary and seven holiday windows, in date order
DECISION = sorted([*DECISION_CUTOFFS, *HOLIDAY_DECISION_CUTOFFS])
raw = load(SUBSET8)
# clock-change hours set to missing, so Prophet fits without them
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
keys = ["unique_id", "ds"]
# one fit per client and window, with the Portuguese holidays as Prophet's holiday table; two processes, and the same
# fits at any count
with_holidays = prophet_windows(df, DECISION, use_holidays=True, workers=2)[keys + ["Prophet"]].rename(
    columns={"Prophet": "WithHolidays"})
without = prophet_windows(df, DECISION, use_holidays=False, workers=2)[keys + ["Prophet"]].rename(
    columns={"Prophet": "NoHolidays"})
forecasts = with_holidays.merge(without, on=keys, validate="one_to_one").merge(
    seasonal_naive(df, DECISION), on=keys, validate="one_to_one")
models = ["WithHolidays", "NoHolidays", "SeasonalNaive"]
# per_client: one MASE per client and model; scored: forecasts beside readings
per_client, scored = score(raw, forecasts, models, SUBSET8, DECISION)

show("decision windows", len(DECISION))
show("holiday decision windows", len(HOLIDAY_DECISION_CUTOFFS))
show("clients", len(SUBSET8))
show("scored hours", len(scored))
# 1 for each hour on a Portuguese national holiday
show("holiday hours in the decision windows", int(is_holiday(scored["ds"]).sum()))
for model in models:
    # the mean of the per-client MASEs, not a pooled error
    show(f"mean MASE {model}", per_client[model].mean(), digits=3)
show("hours where the forecasts differ", int((scored["WithHolidays"] != scored["NoHolidays"]).sum()))
show("clients where holidays help", int((per_client["WithHolidays"] < per_client["NoHolidays"]).sum()))
# the table is kept only on a strictly lower mean; a tie keeps the simpler model, with the table off
show("holiday table kept", "yes" if per_client["WithHolidays"].mean() < per_client["NoHolidays"].mean() else "no")
