"""Prophet with and without the Portuguese holiday table, on the holiday decision windows for SUBSET8 (B-9, B-10): the
four ordinary decision cutoffs and the seven 2014 holidays before Dec 25, before any standard cutoff is scored. Each
variant is scored on the book's MASE scale beside seasonal naive, on the same hours. The table is kept only if it lowers
the mean per-client MASE; a tie keeps the simpler model. The book's Prophet runs take that setting
(lib.compare.PROPHET_HOLIDAYS)."""
from lib.compare import prophet_windows, seasonal_naive, score
from lib.electricity import load
from lib.features import is_holiday
from lib.panel import DECISION_CUTOFFS, HOLIDAY_DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.settings import SUBSET8, show

DECISION = sorted([*DECISION_CUTOFFS, *HOLIDAY_DECISION_CUTOFFS])
raw = load(SUBSET8)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
keys = ["unique_id", "ds"]
with_holidays = prophet_windows(df, DECISION, use_holidays=True, workers=2)[keys + ["Prophet"]].rename(
    columns={"Prophet": "WithHolidays"})
without = prophet_windows(df, DECISION, use_holidays=False, workers=2)[keys + ["Prophet"]].rename(
    columns={"Prophet": "NoHolidays"})
forecasts = with_holidays.merge(without, on=keys, validate="one_to_one").merge(
    seasonal_naive(df, DECISION), on=keys, validate="one_to_one")
models = ["WithHolidays", "NoHolidays", "SeasonalNaive"]
per_client, scored = score(raw, forecasts, models, SUBSET8, DECISION)

show("decision windows", len(DECISION))
show("holiday decision windows", len(HOLIDAY_DECISION_CUTOFFS))
show("clients", len(SUBSET8))
show("scored hours", len(scored))
show("holiday hours in the decision windows", int(is_holiday(scored["ds"]).sum()))
for model in models:
    show(f"mean MASE {model}", per_client[model].mean(), digits=3)
show("hours where the forecasts differ", int((scored["WithHolidays"] != scored["NoHolidays"]).sum()))
show("clients where holidays help", int((per_client["WithHolidays"] < per_client["NoHolidays"]).sum()))
show("holiday table kept", "yes" if per_client["WithHolidays"].mean() < per_client["NoHolidays"].mean() else "no")
