"""Run the held-out week, Dec 25 to Dec 31, 2014: one forecast a day from its own midnight cutoff, with the weekly refit
cycle and the late-data fill. Each forecast is logged when it is made, and its readings are scored as they arrive. The
lead client's last six readings of Dec 28 arrive after the Dec 29 cutoff, so that forecast is made with them filled. A
second run refits on the next day's readings, a deliberate leak, and the check on each refit's inputs fails for it. The
80% bands are calibrated on Dec 9 to Dec 20, 2014, which is earlier than every scored day."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import CAL_DAYS, HELD_OUT_DAYS, REFIT_EVERY, band, coverage_by_day, prepare, run_days, scale_from, with_actuals
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
cal = with_actuals(run_days(df, CAL_DAYS), df)
bands = band(with_actuals(run_days(df, HELD_OUT_DAYS), df), cal, scale)
leaky = with_actuals(run_days(df, HELD_OUT_DAYS, leak=True), df)
in_week = sorted({d for d in bands["refit"] if d >= HELD_OUT_DAYS[0]})
show("refit every (days)", REFIT_EVERY)
show("refit days in the week", ", ".join(f"{d:%Y-%m-%d}" for d in in_week))
show("models used in the week", bands["refit"].nunique())
show("log rows", len(bands))
show("calibration residuals per hour, pooled over clients", cal.dropna(subset=["e"]).groupby("hour").size().iloc[0])
show("log rows whose model read only readings in by its refit day", int((bands["fit_read_by"] <= bands["refit"]).sum()))
show("log rows whose forecast read only readings in by its cutoff", int((bands["read_by"] <= bands["cutoff"]).sum()))
show("leaky log rows whose model read only readings in by its refit day", int((leaky["fit_read_by"] <= leaky["refit"]).sum()))
show("readings that arrived late", int((bands["arrives"] != bands["ds"] + pd.Timedelta(hours=1)).sum()))
show("forecast inputs filled, Dec 29", int(bands.loc[bands["cutoff"] == "2014-12-29", "filled"].iloc[0]))
done = bands.loc[bands["cutoff"] == "2014-12-28", "arrives"].max()
show("Dec 28 complete at", f"{done:%H:%M on %b %d, %Y}")
mae = bands.groupby("cutoff")["ae"].mean()
cov = coverage_by_day(bands)
for day in mae.index:
    show(f"MAE {day:%Y-%m-%d}", mae[day])
for day in cov.index:
    show(f"coverage 80 {day:%Y-%m-%d}", cov[day], digits=3)
show("leaky MAE 2014-12-25", leaky.loc[leaky["cutoff"] == "2014-12-25", "ae"].mean())
