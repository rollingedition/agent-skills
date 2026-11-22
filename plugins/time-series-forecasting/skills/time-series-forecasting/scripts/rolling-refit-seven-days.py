"""Runs the held-out week, Dec 25 to Dec 31, 2014: one forecast a day from its own midnight cutoff, with the weekly refit
cycle and the late-data fill, each logged when it is made. The `log rows` lines show both arrival checks pass, and the
leaky run fails the first. The `MAE` and `coverage 80` lines give each day's mean absolute error and how often its 80%
band held. The 80% bands use calibration days Dec 9 to Dec 20, 2014, earlier than every scored day."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import CAL_DAYS, HELD_OUT_DAYS, REFIT_EVERY, band, coverage_by_day, prepare, run_days, scale_from, with_actuals
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
cal = with_actuals(run_days(df, CAL_DAYS), df)  # the residuals that set the bands, from days earlier than the week
bands = band(with_actuals(run_days(df, HELD_OUT_DAYS), df), cal, scale)
# leak=True refits each day's model on the next day's readings
leaky = with_actuals(run_days(df, HELD_OUT_DAYS, leak=True), df)
# refit dates in the week; the Dec 22 refit is dated before it
in_week = sorted({d for d in bands["refit"] if d >= HELD_OUT_DAYS[0]})
show("refit every (days)", REFIT_EVERY)
show("refit days in the week", ", ".join(f"{d:%Y-%m-%d}" for d in in_week))
show("models used in the week", bands["refit"].nunique())
show("log rows", len(bands))
# hour 0 holds 12 calibration days times 30 clients
show("calibration residuals per hour, pooled over clients", cal.dropna(subset=["e"]).groupby("hour").size().iloc[0])
# a model may read only readings that had arrived by its refit day
show("log rows whose model read only readings in by its refit day", int((bands["fit_read_by"] <= bands["refit"]).sum()))
# a forecast may read only readings that had arrived by its cutoff
show("log rows whose forecast read only readings in by its cutoff", int((bands["read_by"] <= bands["cutoff"]).sum()))
show("leaky log rows whose model read only readings in by its refit day", int((leaky["fit_read_by"] <= leaky["refit"]).sum()))
# a reading arrives at the end of its hour, so any other arrival is late
show("readings that arrived late", int((bands["arrives"] != bands["ds"] + pd.Timedelta(1, unit="h")).sum()))
# every row of a cutoff has the same count, so the first row gives it
show("forecast inputs filled, Dec 29", int(bands.loc[bands["cutoff"] == "2014-12-29", "filled"].iloc[0]))
# the last of Dec 28's readings to arrive
done = bands.loc[bands["cutoff"] == "2014-12-28", "arrives"].max()
show("Dec 28 complete at", f"{done:%H:%M on %b %d, %Y}")
mae = bands.groupby("cutoff")["ae"].mean()
cov = coverage_by_day(bands)
for day in mae.index:
    show(f"MAE {day:%Y-%m-%d}", mae[day])
for day in cov.index:
    show(f"coverage 80 {day:%Y-%m-%d}", cov[day], digits=3)
show("leaky MAE 2014-12-25", leaky.loc[leaky["cutoff"] == "2014-12-25", "ae"].mean())
