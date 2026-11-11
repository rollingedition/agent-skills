---
title: "Time Series Forecasting"
chapter: "Keep the forecast running"
chapter_id: keep-the-forecast-running
book: time-series-forecasting
edition: 2026.11.3
verified: 2026-11-11
edition_code: PAPV-2BKC
canonical: https://rollingedition.com/time-series-forecasting/keep-the-forecast-running
license: CC BY 4.0
attribution: "“Keep the forecast running,” chapter 10 of Time Series Forecasting, Edition 2026.11.3, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/keep-the-forecast-running. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Keep the forecast running

By the end of this chapter you can refit a forecast on a schedule, write each day's forecast to a log before its readings exist, check that the log used only what had arrived, score the log as the readings arrive, flag a day whose error is out of line with the backtest, and say when a model should be retired.

The stake is the next buying round. The supplier commits to power for the next day from the forecast, and a forecast that has gone wrong without anyone noticing costs money in the purchase. This chapter does not reduce that risk to zero. It makes the risk visible on the day it appears, using only what the supplier knew at the time.

The earlier chapters checked the supplier's forecast on past data. Each method was scored after the fact on the last days of 2014, with every reading in hand. In operation the order runs the other way. The supplier buys power for Dec 29, 2014 from a forecast made at 00:00 on Dec 29, the day's cutoff, using only what it knows at that time, and it learns what happened a day later. A forecast that held up on the backtest can drift. The clients change, a holiday falls inside the window, or a meter feed stops for a few hours. The supplier needs to see that before the next buying round, not in a review at the end of the quarter.

This chapter runs the loop for the last seven days of 2014, from Dec 25 to Dec 31. Each day gets one forecast for each of the thirty clients, made from its own midnight cutoff. Every time in this chapter is a data time. A cutoff is 00:00 of its day, and a reading arrives at the end of its hour. The decision and calibration runs start on Nov 25 and Dec 9, 2014, and the refit cycle is anchored to Monday, Nov 24, 2014. All of these start after Jan 16, 2014. That is the first midnight at which the start rule admits all thirty clients into one model: MT_115's first reading is at 00:00 on Jan 14, 2014, and the rule needs 48 hours of history from it, as [Chapter 6](#apply-the-start-rule-to-every-client) sets out.

A forecast says what the readings will do. It does not say why they do it. The loop can tell the supplier that demand has moved away from the forecast. It cannot tell the supplier which habit, price or weather caused the move, and this chapter does not try. A forecast that holds up is not a causal claim, and no flag in this chapter turns into one.

## Refit on a schedule {#refit-on-a-schedule}

A refit re-estimates the model's parameters on the history known at a cutoff. Between refits, the model keeps its trees. Each forecast still reads the most recent readings to build its lag inputs, so the forecast reflects the last hours even when the trees do not.

One detail is often missed. mlforecast 1.1.0 fits each client's scaling again whenever it predicts from a new history: `predict` with `new_df` fits the target transforms on that history (`forecast.py` lines 1374 to 1412, and `core.py` lines 536 to 540 of the pinned release). Each client's mean and spread therefore come from the history known at every cutoff, and only the trees wait for a refit. That is not leakage, because that history is known at the cutoff.

The word needs one caution. In FPP3, `refit()` applies a fitted model without re-estimating it ([FPP3, Chapter 13](https://otexts.com/fpp3/practical.html)). Here, "refit" means re-estimating the trees.

A refit must not use the readings it is about to forecast. A refit at cutoff `c` may read only readings that arrived by `c`. The loop enforces this by construction. The history for a refit, and for every forecast, holds only readings that had arrived by the cutoff, so the actuals of the day being forecast are never in it.

The cadence is the choice that remains. We considered two cadences, a refit every day or a refit every seven days. Both forecast every day from its own cutoff, with the same global model from [Chapter 6](#one-model-for-many-clients): one scaled LightGBM over the thirty clients, with lags of 24 and 168 hours and the client identifier. The global model runs here because it is the best choosable model on the decision windows: the recorded models in Chapter 9 have no forecasts there, so they cannot be chosen. They differ only in how often the trees are re-estimated. The weekly cycle is anchored to Monday, Nov 24, 2014, so its refits fall on Mondays: Nov 24, Dec 1, Dec 8 and so on. A run's refit dates therefore do not depend on the day the run starts. Each forecast uses the model fitted on the Monday on or before its cutoff.

We choose between the cadences on the decision windows: four ordinary days, Nov 25, Nov 26, Dec 2 and Dec 3, 2014. None of them is a Portuguese holiday, and the held-out week is not used. The rule is the lower mean MASE on those days. MASE is the mean absolute error divided by a scale, the in-sample error of the seasonal naive forecast ([FPP3, Chapter 5](https://otexts.com/fpp3/toolbox.html)). Every run in this chapter uses one scale per client, read from readings before Nov 25, 2014 under the rule in [Chapter 2](#take-the-mase-scale-from-history). The decision days, the calibration days and the held-out week share that yardstick. The decision and calibration histories reach back over the clock change of Oct 26, 2014. The loop fills that 01:00 hour from the hours either side, as [Chapter 3](#the-october-hour-that-holds-two) does.

Example `refit-cadence-decision` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""Choose the refit cadence on the decision windows, Nov 25 to Dec 3, 2014. Both cadences forecast every day from its own
cutoff with the global model from Chapter 6. They differ only in how often its parameters are re-estimated: every day, or
every seven days, on Mondays. The held-out week is not used. The last check forecasts each decision day from a model
aged 0 to 6 days, so the claim can be sized to the ages a weekly cadence produces."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import DECISION_DAYS, daily_mase, feed, fit_at, forecast_at, prepare, run_days, scale_from, with_actuals
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
show("decision days", len(DECISION_DAYS))
show("rows read by one refit", len(feed(df, DECISION_DAYS[0])[0]))
names = {1: "daily", 7: "weekly"}
means = {}
for every in names:
    scored = with_actuals(run_days(df, DECISION_DAYS, refit_every=every), df)
    means[every] = daily_mase(scored, scale).mean()
    show(f"refits, {names[every]}", scored["refit"].nunique())
    show(f"MAE, {names[every]}", scored["ae"].mean())
    show(f"mean MASE, {names[every]}", means[every], digits=3)
show("mean MASE, daily minus weekly", means[1] - means[7], digits=3)
show("chosen cadence", names[min(means, key=means.get)])
models = {}
for age in range(7):
    parts = []
    for day in DECISION_DAYS:
        fit_day = day - pd.Timedelta(days=age)
        if fit_day not in models:
            models[fit_day] = fit_at(df, fit_day)[0]
        part, _, _ = forecast_at(models[fit_day], df, day)
        parts.append(part.assign(cutoff=day))
    show(f"mean MASE, model aged {age} days", daily_mase(with_actuals(pd.concat(parts), df), scale).mean(), digits=3)
```

Output:

```text
decision days: 4
rows read by one refit: 40320
refits, daily: 4
MAE, daily: 66.81
mean MASE, daily: 0.754
refits, weekly: 2
MAE, weekly: 67.64
mean MASE, weekly: 0.746
mean MASE, daily minus weekly: 0.008
chosen cadence: weekly
mean MASE, model aged 0 days: 0.754
mean MASE, model aged 1 days: 0.747
mean MASE, model aged 2 days: 0.748
mean MASE, model aged 3 days: 0.741
mean MASE, model aged 4 days: 0.748
mean MASE, model aged 5 days: 0.758
mean MASE, model aged 6 days: 0.750
```

One refit reads 40320 rows, which is thirty clients times 1,344 hours of history. The daily cadence runs 4 refits over the four days, and the weekly cadence runs 2. The mean MASE is 0.754 for daily refits and 0.746 for weekly ones, so the daily cadence is 0.008 higher. A weekly cadence needs half as many fits on these four days, and one seventh of the fits in operation.

The gap is small, and the example does not show that weekly is better. On the decision days, the weekly model is one or two days old. The example therefore also fits a model at each age from 0 to 6 days and forecasts the four decision days from it. Mean MASE runs from 0.741 at three days to 0.758 at five, with a fresh model at 0.754. Age does not show a trend, and the spread across all seven ages is wider than the gap between the two cadences. Four days cannot separate these. The claim is only that a model up to six days old scores near a fresh one on the decision days. Across ages 0 to 6 the mean MASE stays between 0.741, the lowest, and 0.758, the highest, and a fresh model scores 0.754. A reader with a larger model or a longer horizon should run the same check on their own decision days.

The rule picks weekly, because its mean is lower, by 0.008. That gap sits inside the spread that model age alone produces, so the two cadences are close. When they are, the working rule takes the one with fewer refits, and the book says so here: weekly.

**Working rule:** Choose the refit cadence on ordinary days that come before the held-out week, scored on one scale that was read before the first of those days. Take the cadence with the lower mean MASE, and when the two are close, take the one with fewer refits and say so. Never refit on readings from the day you are forecasting.

## Log every forecast before its actuals arrive {#log-every-forecast-before-actuals}

A forecast log is a table with one row for each client and hour. Each row holds the cutoff the forecast was made at, the time the row was written, the client, the hour, the forecast, its lower and upper bounds, the refit day of the model, two arrival times described below, and the count of readings filled for that forecast. The log has one job. It proves what the forecast said at the time, and what the loop could see when it said it. Without it, nobody can tell whether a later report used the forecast that was made, or a forecast rebuilt afterwards from a newer model and the actuals. A rebuilt log is leakage in disguise, because it knows what the forecast should have been.

The band in each row is built the way [Chapter 8](#build-intervals-from-residuals) builds one. It is the forecast plus the scaled residuals of the same hour, taken from the calibration days, Dec 9 to Dec 20, 2014. They come before every held-out day and are fixed before the week begins. Each hour's residuals are pooled over the thirty clients, so each hour has 360 of them, not twelve. Chapter 8's client bands pool the same residuals and are offered at 95% as well. This loop logs the 80% level only, because the retirement trigger in the last section reads the 80% band, and one level keeps the log and the trigger in step. The band is computed from the logged forecast and the fixed calibration residuals, so it needs no reading from the day it covers.

A log proves less than it appears to unless its checks can fail. The rule is that a model and a forecast read only readings that had arrived by the time they were made. The log therefore records two arrival times for each row. `fit_read_by` is the last arrival among the readings the model was fitted on, and it must be no later than the model's refit day. `read_by` is the last arrival among the readings the forecast read, and it must be no later than the cutoff. A comparison of `written_at` with the arrival of a reading would not test this. The replay writes `written_at` as the cutoff, so that comparison passes for any code. In production, `written_at` would come from the append-only store's clock. A replay can only label it.

Example `rolling-refit-seven-days` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
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
```

Output:

```text
refit every (days): 7
refit days in the week: 2014-12-29
models used in the week: 2
log rows: 5040
calibration residuals per hour, pooled over clients: 360
log rows whose model read only readings in by its refit day: 5040
log rows whose forecast read only readings in by its cutoff: 5040
leaky log rows whose model read only readings in by its refit day: 0
readings that arrived late: 6
forecast inputs filled, Dec 29: 6
Dec 28 complete at: 09:00 on Dec 29, 2014
MAE 2014-12-25: 447.59
MAE 2014-12-26: 203.43
MAE 2014-12-27: 54.14
MAE 2014-12-28: 71.67
MAE 2014-12-29: 111.64
MAE 2014-12-30: 87.37
MAE 2014-12-31: 167.15
coverage 80 2014-12-25: 0.232
coverage 80 2014-12-26: 0.431
coverage 80 2014-12-27: 0.790
coverage 80 2014-12-28: 0.764
coverage 80 2014-12-29: 0.713
coverage 80 2014-12-30: 0.782
coverage 80 2014-12-31: 0.701
leaky MAE 2014-12-25: 351.79
```

The rolling example runs the held-out week. Its log has 5040 rows, which is seven days times thirty clients times 24 hours. Every row passes both arrival checks: 5040 pass the first and 5040 pass the second. The week uses two models. The one fitted on Monday, Dec 22, serves Dec 25 to Dec 28, and the one refitted on Monday, Dec 29, serves Dec 29 to Dec 31. The refit therefore falls inside the week.
A check that always passes is worth little on its own, so the example also runs the week with a leak. In that run each day's model is refitted on the next day's readings, so it has seen the day it forecasts. The first check then fails for every row: 0 of the 5040 rows pass. The leak also flatters the forecast. Its MAE on Dec 25 is 351.79 kWh, against 447.59 kWh for the honest run. The check is the thing to keep. An edit that moves a refit onto the next day's readings turns the printed count to zero, and the recorded output then fails.

**Working rule:** Write each forecast's rows at its cutoff, from the readings that have arrived by then, with the refit day and both arrival times beside them. Never rebuild a past log from a newer model or from the actuals. If a day's rows are lost, mark that day as missing in the log, and do not fill it in afterwards.

## Score the log as actuals arrive {#score-the-log-as-actuals-arrive}

A reading scores the forecast logged for its hour when it arrives. The day's score is its daily MASE. For each client, take the mean absolute error over the day's 24 hours and divide it by the client's scale. Then take the mean of those values over the thirty clients:

`daily MASE = mean over clients of (MAE over the day's 24 hours / scale)`

The scale is the one set in the [refit section](#refit-on-a-schedule), read from before Nov 25, 2014, and it does not change from day to day. A reading enters the score for its own day, and only after it has arrived, so the score never uses a value the supplier did not have at the time. That is the second half of the leakage rule in the [log section](#log-every-forecast-before-actuals). A day is scored once its last reading is in. For Dec 29, that is 00:00 on Dec 30.

Most days arrive whole. The held-out week has one day that does not. The lead client's last six readings of Dec 28, 2014, from 18:00 to 23:00, arrive at 09:00 on Dec 29. That is nine hours after the Dec 29 cutoff, so the Dec 29 forecast has to be made without them. The rule for this case is the book's own choice, and no source supports it:

- A reading that has not arrived at a cutoff is left out of that day's refit.
- For the forecast at that cutoff, the missing value is filled with the reading of the same hour a week earlier, which had arrived. The log counts how many values were filled.
- The forecast is not redone when the reading arrives.
- The reading is scored when it arrives, and its day is scored once its last reading is in.

The first option tried was to leave the missing values as they were. The library refused them. At the pinned version, 1.1.0 raised this error when the forecast was made:

```
ValueError: y column contains null values.
```

There are two ways to fill the gap. Forward fill repeats the last reading that arrived. That flattens the evening, because the lead client's 18:00 to 23:00 values all become the 17:00 value, and lag 24 carries that flat evening into the next day's evening forecast. Filling from the same hour a week earlier keeps the evening's shape. The choice was made on the decision windows, not the held-out week.

Example `late-fill-decision` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""Choose how a late reading is filled, on the decision windows, Nov 25 to Dec 3, 2014. For each decision cutoff, the lead
client's last six readings of the day before arrive at 09:00 on the cutoff day, as the Dec 28 readings do in the held-out
week. The forecast for that day fills them in one of two ways: forward from the last reading that arrived, or with the
reading of the same hour a week earlier. Only the lead client's hours 18:00 to 23:00 change, because lag 24 reads them.
The held-out week is not used."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import DECISION_DAYS, LATE_CLIENT, feed, late_copy, prepare, run_days, with_actuals
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
show("readings late for each decision cutoff", feed(late_copy(df, DECISION_DAYS[0]), DECISION_DAYS[0])[2])
errors = {}
for rule in ("forward", "week"):
    parts = []
    for day in DECISION_DAYS:
        scored = with_actuals(run_days(late_copy(df, day), [day], fill=rule), df)
        parts.append(scored.loc[(scored["unique_id"] == LATE_CLIENT) & (scored["hour"] >= 18), "ae"])
    errors[rule] = pd.concat(parts).mean()
    show(f"hours scored, {rule} fill", len(pd.concat(parts)))
    show(f"MAE, lead client hours 18 to 23, {rule} fill", errors[rule])
show("chosen late fill", min(errors, key=errors.get))
```

Output:

```text
readings late for each decision cutoff: 6
hours scored, forward fill: 24
MAE, lead client hours 18 to 23, forward fill: 7.92
hours scored, week fill: 24
MAE, lead client hours 18 to 23, week fill: 5.03
chosen late fill: week
```

The example makes the same six readings late before each decision cutoff and runs both fills. Over the lead client's hours from 18:00 to 23:00, across 24 forecast hours, the mean absolute error is 5.03 kWh with the week-earlier fill, against 7.92 kWh with forward fill. The week-earlier fill wins, and the book uses it in every run.

The held-out week shows the rule at work. 6 readings arrived late, and the Dec 29 forecast filled 6 inputs. The Dec 29 refit left the same six readings out, so the branch that leaves a reading out of a refit runs in this week too. Dec 28 was complete at 09:00 on Dec 29, 2014.

A single day's MAE does not say whether the day was bad, because the level of demand changes from day to day. That is why the flag in the next section divides by a reference.

**Working rule:** Score each day when its last reading arrives, against the forecast logged at its cutoff, on the chapter's one scale. When a reading arrives late, score it then, count it in the log, and leave the logged forecast alone. Never change a forecast after its cutoff, even when the change would improve the score.

## Flag drift against the backtest {#flag-drift-against-the-backtest}

The daily scores from the [last section](#score-the-log-as-actuals-arrive) need a line that says when a day is out of line. A flag is a question about a day, not a verdict. The rule asks whether a day's daily MASE is out of line with what the model did before. A day is flagged when its daily MASE is above twice a reference. The reference is the median daily MASE of the calibration days, Dec 9 to Dec 20, 2014. Those days are earlier than every day the flag judges. None of them is a Portuguese holiday, although Dec 9's lag-24 readings reach back to Dec 8, Imaculada Conceição, a national holiday. That echo is one day's worth, and the median damps it.

The factor of two is the book's rule of thumb. We know of no published threshold for this kind of flag, so the number is ours, and we label it as one. We checked it on the decision windows. The largest ordinary decision day is 1.44 times the reference, and no decision day is flagged at a factor of two (0 flagged). A smaller factor, such as 1.5, would leave little margin over that ordinary day, so a slightly unusual ordinary day could be flagged. We kept two for its margin. Four ordinary days cannot show how often ordinary days get flagged.

Example `drift-flag-rolling` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""Flag drift against the backtest. The reference is the median daily MASE of the calibration days, Dec 9 to Dec 20, 2014,
which are earlier than the held-out week. A day is flagged when its MASE is above FLAG_FACTOR times that median. The
decision days, which are ordinary days, show how the flag behaves before the held-out week."""
from lib.electricity import load
from lib.panel import ALL30
from lib.running import (CAL_DAYS, DECISION_DAYS, FLAG_FACTOR, HELD_OUT_DAYS, daily_mase, flagged, prepare, run_days,
                         scale_from, with_actuals)
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
reference = daily_mase(with_actuals(run_days(df, CAL_DAYS), df), scale).median()
show("reference, median daily MASE", reference)
show("flag above, MASE", FLAG_FACTOR * reference)
decision = daily_mase(with_actuals(run_days(df, DECISION_DAYS), df), scale)
show("largest decision day, times the reference", decision.max() / reference)
show("decision days flagged", len(flagged(decision, reference)))
held = daily_mase(with_actuals(run_days(df, HELD_OUT_DAYS), df), scale)
for day, value in held.items():
    show(f"MASE {day:%Y-%m-%d}", value)
show("held-out days flagged", len(flagged(held, reference)))
show("flagged held-out days", ", ".join(f"{day:%Y-%m-%d}" for day in flagged(held, reference)))
```

Output:

```text
reference, median daily MASE: 0.72
flag above, MASE: 1.43
largest decision day, times the reference: 1.44
decision days flagged: 0
MASE 2014-12-25: 4.62
MASE 2014-12-26: 2.00
MASE 2014-12-27: 0.73
MASE 2014-12-28: 0.76
MASE 2014-12-29: 0.85
MASE 2014-12-30: 0.76
MASE 2014-12-31: 1.14
held-out days flagged: 2
flagged held-out days: 2014-12-25, 2014-12-26
```

The reference is 0.72, so the flag line is 1.43. Across the held-out week, 2 days cross it, Dec 25 and Dec 26. Dec 25 has a daily MASE of 4.62, and Dec 26 has 2.00. Dec 31 comes next at 1.14, below the line.

Both flags have a known cause. Dec 25 is Christmas Day, a Portuguese holiday. The model has no holiday input. [Chapter 5](#measure-what-each-feature-adds) found that calendar and holiday features did not beat plain lags on the subset's decision windows, the holiday ones included, and [Chapter 6](#one-model-for-many-clients) kept none for the global model. Dec 26 is not a holiday in Portugal, but its lag-24 reading is Dec 25. The forecast for each hour of Dec 26 reads the same hour on Dec 25, so the holiday's pattern carries into the next day. These are calendar effects, not drift, and the loop cannot tell the difference. It only flags the days. A person reads each flag and checks the calendar.

One day is not a verdict. A single high day can come from a holiday, a storm or a reading that was entered wrongly. Two flags in a row, with no calendar cause, are a reason to look at the model. The next section says what to do then.

**Working rule:** Flag a day when its daily MASE is above twice the median of the earlier calibration days, and then ask whether a calendar cause explains it. Record the cause beside the flag when there is one. Treat two unexplained flags in a row as the start of a retirement check, never as proof that the model is broken.

## Know when to retire a model {#know-when-to-retire-a-model}

Retiring a model means stopping its use and replacing it. A refit is the lighter move, and it comes first. This chapter names three triggers for either move, and each one reads a number the loop already logs. The first is sustained drift: flags on consecutive days with no calendar cause. The second is an uncovered band: the 80% band covers well under 80% of readings on several days. The third is a change in a library the model depends on.

The second trigger needs a sense of what ordinary coverage looks like. From Dec 27 to Dec 31, coverage at 80% runs 0.790, 0.764, 0.713, 0.782 and 0.701. Dec 29, when the late readings arrive, and Dec 31, New Year's Eve, count as ordinary days here. Dec 25 is lower, at 0.232, and Dec 26 is at 0.431, for the reason the flags gave. Dec 25 is the holiday, and Dec 26 reads it through lag 24. The bands are a little narrow even on ordinary days, as [Chapter 8](#calibrate-on-earlier-windows) found. So a day between 0.70 and 0.80 is normal here, and a day far below that is not.

Its change is invented for the test and is not a fact about the supplier's data. From Dec 27, 2014, every reading of all thirty clients is multiplied by 0.6, as if demand had dropped by 40%. The held-out week then runs on the changed readings, with the same cadence, reference, rule and bands as before.

Example `drift-after-a-change` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""How a change shows up in the flags. This is a stated test, not a fact about the data: from Dec 27, 2014 every reading of
all thirty clients is multiplied by 0.6, as if demand had dropped by 40%. The held-out week runs on the changed readings,
with the same cadence, reference, rule and bands as the examples before it. The calibration days are earlier than the
change, so the bands are fixed before it happens."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import (CAL_DAYS, HELD_OUT_DAYS, band, coverage_by_day, daily_mase, flagged, prepare, run_days,
                         scale_from, with_actuals)
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
cal = with_actuals(run_days(df, CAL_DAYS), df)
reference = daily_mase(cal, scale).median()
changed = df.copy()
after = changed["ds"] >= pd.Timestamp("2014-12-27")
changed.loc[after, "y"] = changed.loc[after, "y"] * 0.6
held = with_actuals(run_days(changed, HELD_OUT_DAYS), changed)
show("reference, median daily MASE", reference)
mase = daily_mase(held, scale)
for day, value in mase.items():
    show(f"MASE {day:%Y-%m-%d}", value)
show("held-out days flagged", len(flagged(mase, reference)))
cov = coverage_by_day(band(held, cal, scale))
for day, value in cov.items():
    show(f"coverage 80 {day:%Y-%m-%d}", value, digits=3)
```

Output:

```text
reference, median daily MASE: 0.72
MASE 2014-12-25: 4.62
MASE 2014-12-26: 2.00
MASE 2014-12-27: 4.74
MASE 2014-12-28: 2.93
MASE 2014-12-29: 1.68
MASE 2014-12-30: 1.78
MASE 2014-12-31: 1.89
held-out days flagged: 7
coverage 80 2014-12-25: 0.232
coverage 80 2014-12-26: 0.431
coverage 80 2014-12-27: 0.078
coverage 80 2014-12-28: 0.179
coverage 80 2014-12-29: 0.328
coverage 80 2014-12-30: 0.328
coverage 80 2014-12-31: 0.333
```

Every day is flagged. Dec 25 and Dec 26 are flagged for Christmas and its echo, as before, and each day from Dec 27, the first changed day, is flagged too. The daily MASE on Dec 27 is 4.74, and coverage falls to 0.078 that day, the lowest of the week.

The scheduled refit on Monday, Dec 29, is the one step in this test that refits on changed readings. It read Dec 27 and Dec 28 at the lower level. Its daily MASE fell from 2.93 on Dec 28 to 1.68 on Dec 29, about 40% lower. It did not clear the flags. Dec 30 and Dec 31 stayed at 1.78 and 1.89, above the line. Coverage recovered to 0.328 and 0.333, still far below 80%.

A run of flags like this, with coverage that low, is a case for an early refit, and the book's rule is to refit early. One scheduled refit here cut the error by about 40% and left the flags standing. We did not test an early refit on a day of its own, so the rule is a rule of thumb and not a measured result.

The third trigger is a library change. Libraries release often, and a later release can change an output even when the code stays the same. The loop depends on 1.1.0 and 4.7.0. Prophet, which Chapter 9 pins at 1.5.0, is not part of this loop, but it is another pinned library, and its release history shows how often such a library moves ([PyPI release history](https://pypi.org/pypi/prophet/json)). A release is a reason to run this chapter's checks again. It is not, by itself, a reason to retire a model. 

These checks are the forecast log, the flags and the coverage of the bands. They are not a monitoring system, which covers alerts, dashboards, data quality across many feeds and the people who respond. A later book on monitoring models in production can continue this case, and this chapter ends where that book would begin.

**Working rule:** Refit early when flags run on several days in a row with no calendar cause, or when the 80% band covers far below 80% of readings on several days, and record the trigger with the log. Retire the model when an early refit does not clear the flags. Re-run this chapter's checks when a pinned library is released, and keep the pins until the checks pass on the new version.

## What goes wrong in production {#what-goes-wrong-ch10}

A feed can stop in the middle of a history. The loop does not fill a reading the feed never delivered. A gap in the middle would shift every lag, so the code raises an error instead. Only the clock-change hours are filled, by [Chapter 3's rule](#mark-clock-change-hours-as-missing). A reading still missing at the end of a history is different, and the [late-data rule](#score-the-log-as-actuals-arrive) handles it.

A refit can leak. If a refit reads the readings of the day it is about to forecast, the backtest looks better than the live run will be. You would notice it as live MASE well above the backtest's for the same days. The loop prevents this by its history rule, and that rule is the one thing to keep when the loop is rewritten. Keep the leak checks from [Chapter 3](#check-a-backtest-for-leakage), the shift test, and from [Chapter 7](#split-a-total-by-share), the poisoning check. The poisoning check writes wrong values over every reading after a cutoff, then confirms that the refit and the forecast at that cutoff do not move.

A flag on the mean of thirty clients can hide a change in one client. A large change in one client moves the daily MASE only by the change in that client's daily MASE divided by thirty. The stress example moves every client at once, so the flags fire. We did not test a change in one client alone. You would notice it as that client's own MASE far above its calibration median. That is the first gap we would close, perhaps with a second flag on each client's own MASE.

A pinned library can still change behaviour when the pin is updated. The null-value error in [the scoring section](#score-the-log-as-actuals-arrive) is behaviour of mlforecast 1.1.0. A later version could fill, drop or accept the gap, and the forecast would change. Updating the pin is a change to the forecast, and it needs the checks to run again.

The last failure is the log written after the fact. Nothing in an example stops a team from rebuilding a log later, and the rebuilt output would look correct. The two arrival columns and their checks are what show it. When those checks are removed, the log stops proving anything.

**Working rule:** Keep three checks in every run: the history rule that keeps the future out of each refit and forecast, the two arrival checks on each log row, and the leak checks from Chapters 3 and 7. When one of them fails, stop the loop and fix the cause before the next forecast. Do not repair a history or a log by hand, because a hand repair is the kind of change the checks exist to catch.

## Decisions this chapter made {#decisions-ch10}

- **Refit cadence:** every seven days, on Mondays. The decision windows gave 0.746 against 0.754, a gap inside the spread that model age alone produces, so the tie-break applies and the book takes the cadence with fewer refits.
- **One MASE scale:** read from the readings before Nov 25, 2014, and used for every run in this chapter, following the rule in [Chapter 2](#take-the-mase-scale-from-history). A decision day, a calibration day and a held-out day are therefore scored on one yardstick, and no scored hour helped set it.
- **Flag rule:** a day is flagged above twice the median daily MASE of the calibration days, Dec 9 to Dec 20, 2014. The factor of two is a labelled rule of thumb, kept for its margin over the ordinary decision days.
- **Bands:** 80% only, from the scaled residuals of the same hour, pooled over the thirty clients, from the twelve calibration days, fixed before the held-out week. Chapter 8's client bands pool the same residuals and are offered at 95% as well. This loop logs 80% because the retirement trigger reads that level. It logs no total forecast, total band or purchase quantile, so it checks the client forecasts and not the purchase that Chapter 8 makes against the total. A supplier who buys against the total would add that quantile to the log.
- **Late readings:** left out of the refit, filled from the same hour a week earlier for the forecast, counted in the log, scored when they arrive, and never used to redo a forecast. The fill was chosen on the decision windows. The rule has no source and is the book's own.
- **Scope:** seven days for thirty clients. A week holds a holiday, a late reading and a weekly refit that falls inside it, so it shows each rule. A longer run would measure how often ordinary days get flagged, which this chapter does not measure.
- **Monitoring boundary:** this chapter's checks only. The monitoring system that would watch them over time is outside this book.
- **Your own case:** the book's last decision hands the work back. The supplier's case ends here: a weekly refit, a log that checks what each forecast read, scoring as the readings arrive, and a flag against the backtest. Your case needs these decisions made again on your own data: the refit cadence on your ordinary decision days, the late-data rule on the feed you actually receive, the flag factor on your calibration days, and the band level your buying rule needs. Make each one on days before your held-out week.
