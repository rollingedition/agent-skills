---
title: "Time Series Forecasting"
chapter: "Set the baselines a model must beat"
chapter_id: beat-the-naive-baselines
book: time-series-forecasting
edition: 2026.11.17
verified: 2026-11-22
edition_code: QG16-GENM
canonical: https://rollingedition.com/time-series-forecasting/beat-the-naive-baselines
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Set the baselines a model must beat,” chapter 2 of Time Series Forecasting, Edition 2026.11.17, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/beat-the-naive-baselines. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Set the baselines a model must beat

In this chapter you compute three baselines for a client's day-ahead forecast, naive, seasonal naive and average of weeks, and scale a client's error with MASE, using a scale that reads only the readings before the forecast week.

[Chapter 1](#score-on-a-held-out-week) ended with two scores on the held-out week, and neither can be judged yet, because an error in kWh means nothing on its own. The supplier, whose purchase rests on each hour's forecast, has to set each model's error against what the simplest forecast scores on the same hours, and against how much the client's demand moves from one day to the next. This chapter builds both comparisons. The supplier needs them before it can say that a model is worth its cost.

Every error is a miss in kilowatt hours for one hour, and the scores here are hourly averages of those misses. A baseline's score is the same kind of number. It says how many kilowatt hours of error the simplest rule leaves for an average hour of the day, and a model that cannot beat that figure has not earned its extra cost. So each score is read against the lead client's mean demand as well as against the other rows.

## Why a baseline comes first {#why-a-baseline-comes-first}

A baseline is a forecast that needs no fitting. It copies a value the history already holds, so it costs almost nothing to run, and it sets a bar that any model has to clear. A model earns its place only by beating a forecast that cost nothing. Fitting time, tuning and keeping a model running are all costs, and the baseline's score measures what those costs buy.

Three terms matter here. The [cutoff](#the-case-and-its-data) is the hour at which a forecast is made. The cutoff is the first hour the forecast covers, and the history is every reading before the cutoff, all that a forecast may use, though the book's models fit on its last eight weeks. The [horizon](#the-case-and-its-data) is how far ahead a forecast reaches, here 24 hours. A [window](#the-case-and-its-data) is one cutoff together with the horizon it covers, and a backtest is the score of many windows, each made as it would have been made on its day.

The comparison has to be fair, or it measures the setup and not the model. A baseline scored on different hours, with a different history or a different scoring routine, says nothing about the model beside it. So every method in this chapter takes its cutoffs from `held_out_cutoffs()`, the seven daily cutoffs at 00:00 of the held-out week, reads its history through `history_before()`, which takes the eight weeks of hours before a cutoff, and is scored by the same code. These are the seven windows [Chapter 1](#score-on-a-held-out-week) used.

**Working rule:** Score every baseline on the same windows, histories and scoring code as the model it will be compared with, and count each baseline's missing forecasts before you read its score. A model that beats a baseline scored on different hours has not beaten it.

## Three baselines to beat {#three-baselines-to-beat}

Each baseline copies the history in a different way. Naive carries the last hour it has seen forward across the whole day. Seasonal naive copies the day before, hour for hour. Average of weeks takes the mean of that hour on that weekday over the four weeks before.

Every rule covers the 24 hours after a cutoff. Call the cutoff `T`, the hour at which the forecast is made, and let `k` run from 0 to 23 across the hours the forecast covers. The three rules are these:

- Naive repeats the last reading before the cutoff: `forecast(T + k) = y(T - 1)`.
- Seasonal naive repeats the reading one day earlier: `forecast(T + k) = y(T + k - 24)`.
- Average of weeks takes the mean of the same hour on the same weekday over the four weeks before: `forecast(T + k) = (y(T + k - 168) + y(T + k - 336) + y(T + k - 504) + y(T + k - 672)) / 4`.

The lags are in hours, so 168 is one week. Every reading a rule uses comes from before the cutoff: naive's is the hour before it, seasonal naive's are the 24 hours before it, and average of weeks reaches back one to four weeks. Take the window at 00:00 on Dec 25, 2014 as a worked case. Naive gives every hour of Dec 25 the reading at 23:00 on Dec 24, so the forecast is flat. Seasonal naive gives 00:00 on Dec 25 the reading at 00:00 on Dec 24, and so copies the whole previous day's shape. Average of weeks gives 00:00 on Dec 25 the mean of the 00:00 readings on Dec 18, Dec 11, Dec 4 and Nov 27. That mean smooths out one unusual day, but it also averages in any level change across the four weeks.

Each rule fails in a known way. Naive gives every hour of the day the same value, so it cannot follow the daily peak at all. Seasonal naive copies one day, so an unusual day is copied into the forecast for the next day, as the per-day errors later in this section show on the held-out week. Average of weeks needs four clean weeks, and a holiday in any of them enters the mean with the same weight as an ordinary day. A baseline's score therefore describes its rule on the windows it was run on, and these failures show up only on the windows where they happen.

Naive and seasonal naive come from statsforecast (2.1.1), whose classes `Naive` and `SeasonalNaive` are in `statsforecast/models.py`. The seasonal naive rule is the one [Hyndman and Athanasopoulos](https://otexts.com/fpp3/toolbox.html#sec-simple-methods) give for seasonal data: the forecast is the last observed value from the same season. Average of weeks is not a library method, so `examples/lib/baselines.py` computes it in pandas, where the rule can be read, and each window reads only its own history. A lag missing from that history raises an error instead of being skipped. One script scores all three rules through those seven windows, and its first lines count the windows, scored hours and missing forecasts, so you can check them before you read a score.

Example `naive-baselines-held-out-week` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.17:

```python
"""Score the three baselines for the lead client over the held-out week, on the same seven windows. The point rests on the missing-forecasts line, which must be zero for the scores to compare, and on the three MAE lines."""
import pandas as pd

from lib.backtest import held_out_cutoffs, score_windows, window_mae
from lib.baselines import BASELINES, baseline_forecasts
from lib.electricity import load
from lib.settings import LEAD, show

cutoffs = held_out_cutoffs()                                 # seven daily cutoffs at 00:00; every baseline uses these same windows
df = load([LEAD])[["unique_id", "ds", "y"]]                  # unique_id, ds and y only: the baselines read no other column
forecasts = baseline_forecasts(df, cutoffs)                  # one row per forecast hour, one column per baseline; each window reads its own history
labels = ["naive", "seasonal naive", "average of weeks"]     # printed names, in the order of BASELINES, which the loops below zip with

show("windows", len(cutoffs))
show("scored hours", len(forecasts))
show("missing forecasts", int(forecasts[BASELINES].isna().sum().sum()))   # NaN marks a forecast that could not be made; the two sums count them over every column
show("mean demand", df[df["ds"].isin(forecasts["ds"])]["y"].mean())       # the mean over the scored hours only, not over the whole history
for model, label in zip(BASELINES, labels):
    show(f"{label} MAE", score_windows(df, forecasts, model)["mae"])      # pooled over every scored hour; the result is keyed by metric name
for model, label in zip(BASELINES, labels):
    per_window = window_mae(df, forecasts, model)                         # one MAE per window, keyed by the day its forecast hours fall on
    show(f"{label} worst window MAE", per_window.max())
    show(f"{label} worst window", per_window.idxmax().strftime("%b %d, %Y"))
    for day in ["2014-12-25", "2014-12-26"]:                              # Dec 25 is the holiday and Dec 26 the day after: the two windows the prose reads
        show(f"{label} MAE {pd.Timestamp(day):%b %d} window", per_window[pd.Timestamp(day)])   # windows are keyed by midnight of their day, so a Timestamp at 00:00 finds one
```

Output:

```text
windows: 7
scored hours: 168
missing forecasts: 0
mean demand: 46.62
naive MAE: 8.16
seasonal naive MAE: 8.36
average of weeks MAE: 8.96
naive worst window MAE: 11.01
naive worst window: Dec 30, 2014
naive MAE Dec 25 window: 5.84
naive MAE Dec 26 window: 10.36
seasonal naive worst window MAE: 12.16
seasonal naive worst window: Dec 26, 2014
seasonal naive MAE Dec 25 window: 9.41
seasonal naive MAE Dec 26 window: 12.16
average of weeks worst window MAE: 22.09
average of weeks worst window: Dec 25, 2014
average of weeks MAE Dec 25 window: 22.09
average of weeks MAE Dec 26 window: 12.33
```

The three scores are comparable only because they cover the same hours: 168 scored hours in 7 windows, one for each hour of the seven days, and 0 missing forecasts across the three rules. That count is the one the [working rule in the first section](#why-a-baseline-comes-first) asks for, and zero is the only value that lets the three be compared on the same hours.

Read each error below against the lead client's mean demand of 46.62 kWh. Each score below is a [MAE](#score-on-a-held-out-week), the mean absolute miss in kWh that [Chapter 1](#score-on-a-held-out-week) defines. The three baselines score:

- naive: 8.16 kWh
- seasonal naive: 8.36 kWh
- average of weeks: 8.96 kWh

The simplest rule has the lowest error on this week, and average of weeks, which averages four weeks, is the weakest. Nothing here explains that order, and this is one client and one week, so it is a result for this week only. Chapter 3 is where the book backtests seasonal naive across many cutoffs.

The totals hide where the errors sit. The week begins on Dec 25, 2014, a Portuguese national holiday, and its first window is where the rules part company. Naive has the lowest error on it, at 5.84 kWh, against 9.41 kWh for seasonal naive. Average of weeks is worse still, and its largest error of the week falls on that window, at 22.09 kWh, because its four lags are ordinary days and the holiday has no match among them.

The day after the holiday is where copying costs seasonal naive. Its largest error of the week falls on Dec 26, 2014, at 12.16 kWh, because that window copies the holiday's pattern. On that day naive is still the lowest, at 10.36 kWh.

Figure 2.1 draws seven windows, three bars a day: naive, seasonal naive, hatched average of weeks. The lowest bar changes 3 times; no baseline is lowest every day.

*Figure 2.1. Each baseline's MAE in each window.*

![No baseline is lowest in every window, so one week names no winner](https://rollingedition.ai/books/time-series-forecasting/2026.11.17/figures/baseline-window-errors.svg)

Example `figure-baseline-window-errors` (Python 3.13.16 · matplotlib 3.11.2 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.17:

```python
"""Score the three baselines on each of the seven held-out windows, and draw each window's MAE as a group of three bars.
The printed count says how often the lowest baseline changes from one window to the next."""
import numpy as np
import pandas as pd

from lib.backtest import held_out_cutoffs, scoring_counts, window_mae
from lib.baselines import BASELINES, baseline_forecasts
from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.settings import LEAD, show

cutoffs = held_out_cutoffs()                                 # the same seven windows as naive-baselines-held-out-week
df = load([LEAD])[["unique_id", "ds", "y"]]
forecasts = baseline_forecasts(df, cutoffs)
labels = ["naive", "seasonal naive", "average of weeks"]     # printed names, in the order of BASELINES

for model in BASELINES:
    assert scoring_counts(df, forecasts, model)["missing_forecasts"] == 0   # a missing forecast would drop out of its window's MAE
mae = pd.DataFrame({label: window_mae(df, forecasts, model) for model, label in zip(BASELINES, labels)})   # rows: window days; columns: baselines
leader = mae.idxmin(axis=1)                                  # the baseline with the lowest MAE in each window
assert all(row.nsmallest(2).iloc[0] < row.nsmallest(2).iloc[1] for _, row in mae.iterrows())   # no two baselines tie for a window

show("windows", len(mae))
# leader.shift() is NaN for the first window, so the comparison starts at the second
show("changes of lowest baseline between neighbouring windows", int((leader != leader.shift()).iloc[1:].sum()))

fig, ax = new_figure(height=2.8)
x = np.arange(len(mae))
width = 0.27                                                 # three bars per window; offset (i - 1) puts the middle bar on the tick
for i, (label, color) in enumerate(zip(labels, (ACCENT, INK, MUTED))):
    hatch = "//" if label == "average of weeks" else ""      # a pattern too, so the third bar is not told apart by colour alone
    ax.bar(x + (i - 1) * width, mae[label].values, width, color=color, label=label, hatch=hatch, edgecolor=INK, linewidth=0.6)
ax.set_axisbelow(True)                                       # grid lines stay behind the bars
ax.set_xticks(x, [f"{day:%b} {day.day}" for day in mae.index])
ax.set_xlabel("window, by the day its forecast hours fall on")
ax.set_ylabel("MAE in the window, kWh")
ax.set_ylim(bottom=0)
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "baseline-window-errors")
```

Output:

```text
windows: 7
changes of lowest baseline between neighbouring windows: 3
figure: figures/baseline-window-errors.svg
```

We recommend reporting all three baselines every time. Use seasonal naive as the main reference for [MASE](#scale-errors-with-mase), because it carries the daily cycle that makes hourly demand predictable, and keep naive beside it, because on some weeks the flat rule is the stronger one.

**Working rule:** Start from naive and seasonal naive, both from the library, and add average of weeks when the series has a weekly rhythm worth testing. Check one forecast by hand against its formula before you rely on a baseline: pick one cutoff, compute one hour from the readings in its history, and compare the result with the forecast.

## Scale errors with MASE {#scale-errors-with-mase}

A kilowatt-hour error means different things for different clients. A miss of 8.36 kWh an hour is small for a client that uses 46.62 kWh an hour, and the same miss would be large for a hypothetical client that uses 4 kWh an hour. Scaling the error removes that difference. A scaled error divides each error by a scale, the typical error of a simple method on the same client's own history. MASE, the mean absolute scaled error, is the mean of the absolute scaled errors. [Hyndman and Koehler](https://robjhyndman.com/papers/mase.pdf) introduced it in a 2006 paper in the *International Journal of Forecasting*. The link is the authors' preprint, dated 2005. They noted that the scaled error does not depend on the units of the data, so the same number can be read across clients of very different size. This chapter scores one client, so that comparison across clients is the reason for the scale, not a result shown here.

The 2006 paper scales by the one-step naive error: the mean absolute difference between each reading and the one before it. That is the natural scale for non-seasonal series. For hourly demand, this book uses the seasonal form that [Hyndman and Athanasopoulos](https://otexts.com/fpp3/toolbox.html#sec-accuracy) give for seasonal data, because the comparison a reader wants is with seasonal naive: under the seasonal scale, the denominator is seasonal naive's error on the client's own history. A MASE below 1 then says the forecast's error on the scored hours is smaller than seasonal naive's error on that history. A one-step scale would compare it with a method this book does not use for hourly demand.

The two formulas are these:

- `scale = mean of |y(t) - y(t - 24)|` over every reading t before the first test day, with the pairs that touch a masked clock-change hour left out
- `MASE = mean of |actual(t) - forecast(t)| / scale` over the scored hours

The scale reads every reading before the first test day, 17352 hours, about two years. That is longer than each window's eight-week history, and a longer history gives a steadier estimate of the client's usual swing. One scale for the week also means every window is read against the same number. The function `seasonal_scale` in `examples/lib/baselines.py` computes it for one client or for many, and returns one value per client. To see whether the cut matters, score the three baselines on the held-out week twice: with the scale from history, and with the scale from the whole series, both with the clock-change readings masked.

Example `mase-scale-leak-check` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.17:

```python
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
```

Output:

```text
scale rows from history: 17352
last scale reading from history: Dec 24, 2014 23:00
scale rows from whole series: 17520
last reading of whole series: Dec 31, 2014 23:00
test week share of whole-series rows in percent: 0.959
clock-change rows in scale history: 4
test week own mean day-to-day difference: 8.3607
scale from history as recorded: 7.1121
scale from history clock changes masked: 7.1005
scale from whole series clock changes masked: 7.1126
naive MASE from history scale: 1.15
naive MASE from whole-series scale: 1.15
naive MASE ratio whole-series over history: 0.9983
seasonal naive MASE from history scale: 1.18
seasonal naive MASE from whole-series scale: 1.18
seasonal naive MASE ratio whole-series over history: 0.9983
average of weeks MASE from history scale: 1.26
average of weeks MASE from whole-series scale: 1.26
average of weeks MASE ratio whole-series over history: 0.9983
seasonal naive MASE from history scale at four decimals: 1.1775
seasonal naive MASE from whole-series scale at four decimals: 1.1755
```

The scale from history is 7.1005 kWh, the average gap between each hour and the same hour the day before, and it reads against the mean demand the way an MAE does. A scale that is a large share of the mean says the client's own day-to-day swing is large, and every error for that client is read against that swing. Dividing seasonal naive's MAE of 8.36 kWh by the scale gives its MASE, 1.18. utilsforecast's `mase`, reached through the helper `mase_scores`, computes this MASE by dividing the same MAE by the same seasonal scale (utilsforecast 0.2.17, `utilsforecast/losses.py`, function `mase`), so the division by hand gives the same figure.

utilsforecast (0.2.17) computes MASE with its `mase` function in `utilsforecast/losses.py`. The function takes its scale from the `train_df` it is given, and it shifts that frame by rows, not by time, so a missing hour moves every later lag and nothing reports it. It also needs sorted input. Its time filter runs only when the scored frame has a `cutoff` column (function `_create_train_with_cutoffs`). So the library does not decide which readings the scale may read. The caller does, and the next section is about that choice.

**Working rule:** Report MASE beside MAE whenever the clients you compare differ in size, and say in the same sentence which history the scale comes from. Read MASE as a ratio of two mean errors, one from the scored hours and one from the history. It is not a percentage gain over seasonal naive, even when the MASE is well below 1.

## Take the MASE scale from history {#take-the-mase-scale-from-history}

A scale describes the history before the first test day, not the series as a whole. If the scale reads the whole series, it also reads the hours the forecast is scored on, so the held-out week enters the denominator of its own error. That is a [leak](#keep-the-future-out-of-history), and it raises no error. The MASE it produces looks like any other. The rule in this book is that a scale reads only the readings before the first test day of the week it scores, which for the held-out week is Dec 25, 2014.

A whole-series scale looks like the safer choice, because it uses more readings. It uses more readings from the wrong period. The extra readings are the ones the forecast is judged on, so the scale is no longer a measure of what was known at the cutoff. More data does not fix that. Only the cut does.

The script in [the previous section](#scale-errors-with-mase) prints the rows each scale reads, and those lines are the check. The history scale reads 17352 readings, and its last reading is Dec 24, 2014 23:00, the hour before the first test day. A later date there would mean test hours reached the scale.

The whole-series scale reads 17520 readings, through Dec 31, 2014 23:00, which covers the whole held-out week. Both scales have their clock-change readings masked, so the held-out week is the only difference between them.

The whole-series scale is the larger one, so every MASE computed with it is smaller. At two decimals both scales give seasonal naive 1.18, so the leak does not show. At four decimals it does, with seasonal naive's MASE at 1.1775 against 1.1755, and the factor below is the lesson, not the rounding.

The scales are 7.1005 kWh from history and 7.1126 kWh from the whole series, and the same factor, 0.9983, shrinks each of the three rules.

The leak is small on this week because the held-out week is a small share of the series. It makes up 0.959 percent of the whole-series readings, so the whole-series scale is roughly the history scale moved toward the held-out week's own swing by that share. The held-out week's own mean day-to-day difference is 8.3607 kWh, against 7.1005 kWh for the history, so the week swings more than the history does. The share times that gap is the leak, and the ratio above is its size. The leak grows in two ways. It grows when more of the scale's rows are test hours, as in a test period much longer than one week, such as the year of cutoffs in Chapter 3. It also grows when the held-out week's swing sits further from the history's. A quieter week would pull the whole-series scale down and make every MASE larger, so the same leak can flatter a model in one week and penalise it in another.

The clock changes are a second, smaller point, and this chapter handles them as Chapter 3 does. The history holds 4 clock-change readings: the two gap hours and the two repeat hours of the March and October changes in 2013 and 2014. The gap hours read zero, and the repeat hours hold the energy of two, as the [data card](https://github.com/rollingedition/book-time-series-forecasting/blob/b70a7daceabaf9b17aa6f2623cf21720bcfc27d7/examples/data/README.md) describes; [Chapter 3](#the-october-hour-that-holds-two) shows the effect. Kept as recorded, those pairs give a scale of 7.1121 kWh. Masked, the scale is 7.1005 kWh, because the pairs that touch a masked reading drop out of the mean. A masked reading is neither zero nor a copy; it is missing. The chapter's scale masks them, and [Chapter 3 gives the reason](#meet-the-clock-changes), which sets them to missing in every training set and every score.

**Working rule:** Pass a scale only the readings before the first test day, mask its clock-change readings, and print the last reading it uses. Check that this reading is the hour before the first test day. A small difference between the two scales does not show the procedure is right. The row check does.

## Read a baseline's score {#read-a-baselines-score}

MASE compares a forecast with seasonal naive's error on the client's own history. Below 1, the forecast's error on the scored hours is smaller than the error seasonal naive made on that history; above 1, it is larger. [Hyndman and Koehler](https://robjhyndman.com/papers/mase.pdf) state this reading in their paper for the one-step scale, and the arithmetic is the same for the seasonal scale. The book gives no threshold for a good score. What counts as good depends on what a miss costs the supplier, which the supplier knows and this book does not.

The table puts the three baselines side by side, one row each. The MAE is in kWh, and the MASE uses the history scale with the clock changes masked. The leak from [the previous section](#take-the-mase-scale-from-history) does not show at two decimals, so the table has one MASE column.

| Baseline | MAE (kWh) | MASE |
| --- | --- | --- |
| Naive | 8.16 | 1.15 |
| Seasonal naive | 8.36 | 1.18 |
| Average of weeks | 8.96 | 1.26 |

All three MASE values are above 1, so every baseline missed by more than seasonal naive's typical error on the history. For seasonal naive itself, the week's day-to-day swing was larger than the history's. Its MAE equals the held-out week's own day-to-day difference, 8.3607 kWh, against 7.1005 kWh for the history. For naive and average of weeks, the scale compares them with seasonal naive, not with their own past, so this table does not say how those two rules did on the history. The week opens on a national holiday, and the [earlier section](#three-baselines-to-beat) shows the holiday window as the largest error for average of weeks. The book does not test the remaining days here.

The order is the same on both measures, naive first, seasonal naive second and average of weeks third. That agreement is not a finding. MASE divides every MAE by the same scale, so the order cannot differ between MAE and MASE for one client.

The table also raises the supplier's question: is the simplest rule good enough to buy on? That depends on what an hour of error costs, and the MASE does not price it. What the MASE gives the supplier is a comparison it can repeat. A later model can be scored with the same helpers, so its MASE sits beside these rows without a change of units.

Take the table in this order. First, confirm from the [earlier section](#three-baselines-to-beat) that every row scores the same hours, with no missing forecasts. Second, read the MASE column against 1. Third, compare each row with the others, not with a number from a textbook. A fitted model that is only as good as the best row has not shown much, and one that is better by less than the printed rounding has not shown anything at all.

**Working rule:** Read each baseline's MASE against 1 and against the other baselines, and do not name a winner on one week. A model counts as better only when it beats the best baseline on more than one set of windows, and when the margin is larger than the rounding of the printed scores.

## What goes wrong in production {#what-goes-wrong-ch2}

Score a baseline on other hours, or with another history, and the comparison stops meaning what it says. A team may score its model on a year of cutoffs and its baseline on one week, or give the model a longer history than the baseline. The comparison then measures the setup, and the printed numbers look like evidence. The check is the one this chapter uses. Every method takes its cutoffs from `held_out_cutoffs` and its history from `history_before`, and the count of missing forecasts is printed for each run.

[The leak in the scale](#take-the-mase-scale-from-history) leaves a MASE that looks like any other, and raises no error. In this chapter it multiplies every seasonal naive MASE by 0.9983, a change that two decimals hide. A larger leak in another week would look the same on the page. The check is the printed row count and the last reading the scale uses, both on one line of output that a reviewer can read without rerunning anything.

A gap in the seasonal lag gives a wrong scale that no output marks. With a missing hour, a lag of 24 rows reaches 25 hours back, so each pair for the next day compares the wrong hours. The library's `mase` has no gap check of its own. The helper `seasonal_scale` checks that each client's hours are unbroken, and `mase_scores` runs the same check on the scale's rows before the library reads them. The check raises an error rather than using an assertion, because Python removes assertions under `-O`. The scored hours are checked only for a reading and for duplicates. A production run should count the hours in the feed before it computes any scale, because a check inside the helper reports the problem after it has reached the scale.

The seasonal lag can also be chosen for the wrong cycle. A lag of 24 suits hourly demand with a daily cycle. Daily data has a weekly cycle, and hourly data with a weekly rhythm may need a lag of 168 instead. A scale computed with the wrong season is still a number, so nothing in the output shows the mistake. The check is to name the season beside the scale in the prose and to confirm it against the data's cycle before the scale is used.

Picking a setting on the held-out week spoils the comparison. Average of weeks has a choice in it: how many weeks to average. If that number is picked because it gives the best score on the held-out week, the baseline has been fitted to the week it is judged on, and the comparison with the models is no longer fair. This book fixed four weeks before any score was printed, and this chapter keeps it for every window. A change to it belongs in the decision list at the end of the chapter, made before the scores are seen.

**Working rule:** Check a baseline's inputs, and its scale's, in this order: the same windows for every method, a scale that reads only earlier readings with its last reading printed, an unbroken hourly history for the seasonal lag, and a season that matches the data's cycle. Each check is one line of output or one count, and a failed check stops the comparison until it is fixed.

## Decisions this chapter made {#decisions-ch2}

Seven choices shaped this chapter, and the last is its hand-off to Chapter 3. Most are in `examples/lib/baselines.py`, the baseline helpers, so a fix there reaches every chapter that calls them. The history length and the horizon are the settings in `examples/lib/settings.py`, the same ones [Chapter 1](#decisions-ch1) used, so no baseline here reads a different history from the forecasts beside it.

- The MASE scale is seasonal, with a lag of 24 hours. The one-step scale of the 2006 paper is not used.
- The scale is one number per client for the held-out week, from every reading before Dec 25, 2014. It is longer than each window's history, as set out above. utilsforecast can take a scale per cutoff when the frame carries a cutoff column, but this chapter does not use that option. If you add one, know that its filter keeps `ds <= cutoff`, so the cutoff hour itself is included. A cutoff in this book is the first hour a forecast covers, and its reading is not history. A cutoff column built from this book's cutoffs must therefore be shifted back one hour first.
- Average of weeks uses the four weeks before each forecast day, is computed in pandas, and reads only its own eight-week history.
- Naive and seasonal naive are the statsforecast classes. Scores are pooled over every scored hour of the week and printed to two decimals.
- The scale masks its 4 clock-change readings, following Chapter 3's rule. The printed history scale is then 7.1005 kWh.
- The baselines draw no random numbers, so the examples set no seed.
- Chapter 3 keeps seasonal naive and these helpers and runs them over a year of Sunday cutoffs, with one scale per client taken from every reading before the first cutoff, the rule this chapter sets out. One week cannot give that test.
