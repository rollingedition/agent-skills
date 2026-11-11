---
title: "Time Series Forecasting"
chapter: "Set the baselines a model must beat"
chapter_id: beat-the-naive-baselines
book: time-series-forecasting
edition: 2026.11.2
verified: 2026-11-11
edition_code: RHYP-H8RM
canonical: https://rollingedition.com/time-series-forecasting/beat-the-naive-baselines
license: CC BY 4.0
attribution: "“Set the baselines a model must beat,” chapter 2 of Time Series Forecasting, Edition 2026.11.2, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/beat-the-naive-baselines. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Set the baselines a model must beat

By the end of this chapter you can compute three baselines for a client's day-ahead forecast, naive, seasonal naive and average of weeks, and scale a client's error with MASE, using a scale that reads only the readings before the forecast week.

Chapter 1 ended with two scores on the held-out week, one for seasonal naive and one for AutoETS, and neither can be judged yet. An error in kWh means nothing on its own. It has to be set against what the simplest forecast scores on the same hours, and against how much the client's demand moves from one day to the next. This chapter builds both comparisons. The supplier needs them before it can say that a model is worth its cost.

The supplier buys each hour of the next day, so every error is a miss in kilowatt hours for one hour. A baseline's score is the same kind of number. It says how many kilowatt hours of error the simplest rule leaves for an average hour of the day, and a model that cannot beat that figure has not earned its extra cost. The scores in this chapter are therefore hourly averages, and each one is read against the lead client's mean demand as well as against the other rows.

## Why a baseline comes first {#why-a-baseline-comes-first}

A baseline is a forecast that needs no fitting. It repeats a value the history already holds, so it costs almost nothing to run, and it gives a score that any model has to beat. A model earns its place only by scoring better than a forecast that cost nothing. Fitting time, tuning and the work of keeping a model running are all costs, and the baseline's score is the measure of what those costs buy.

Three terms matter in this chapter. A cutoff is the hour at which a forecast is made. It is the first hour the forecast covers, and the history is every reading before it. The horizon is how far ahead a forecast reaches, here 24 hours. The window is one cutoff together with the horizon it covers. A backtest is the score of many windows, each made as it would have been made on its day.

The comparison has to be fair, or it measures the setup and not the model. A baseline scored on different hours, with a different history, or with a different scoring routine, says nothing about the model beside it. Every method in this chapter therefore takes its cutoffs from `held_out_cutoffs()`, which gives the seven daily cutoffs at 00:00 of the held-out week. It reads its history through `history_before()`, which takes the eight weeks of hours before a cutoff, and it is scored by the same code. The seven windows are the ones Chapter 1 used.

**Working rule:** Score every baseline on the same windows, histories and scoring code as the model it will be compared with, and count each baseline's missing forecasts before you read its score. A model that beats a baseline scored on different hours has not beaten it.

## Three baselines to beat {#three-baselines-to-beat}

Each baseline is a rule for the 24 hours after a cutoff. Call the cutoff `T`, the hour at which the forecast is made, and let `k` run from 0 to 23 across the hours the forecast covers. The three rules are these:

- Naive repeats the last reading before the cutoff: `forecast(T + k) = y(T - 1)`.
- Seasonal naive repeats the reading one day earlier: `forecast(T + k) = y(T + k - 24)`.
- Average of weeks takes the mean of the same hour on the same weekday over the four weeks before: `forecast(T + k) = (y(T + k - 168) + y(T + k - 336) + y(T + k - 504) + y(T + k - 672)) / 4`.

The lags are in hours, so 168 is one week. Every reading a rule uses comes from before the cutoff: naive's is the hour before it, seasonal naive's are the 24 hours before it, and average of weeks reaches back one to four weeks. Take the window at 00:00 on Dec 25, 2014 as a worked case. Naive gives every hour of Dec 25 the reading at 23:00 on Dec 24, so the forecast is flat. Seasonal naive gives 00:00 on Dec 25 the reading at 00:00 on Dec 24, and it copies the whole previous day's shape. Average of weeks gives 00:00 on Dec 25 the mean of the 00:00 readings on Dec 18, Dec 11, Dec 4 and Nov 27. That mean smooths out one unusual day, but it also averages in any level change across the four weeks.

Each rule fails in a known way, visible in its formula. Naive gives every hour of the day the same value, so it cannot follow the daily peak at all. Seasonal naive copies one day, so an unusual day is copied into the forecast for the next day. The held-out week shows this, as the per-day errors later in this section do. Average of weeks needs four clean weeks, and a holiday in any of them enters the mean with the same weight as an ordinary day. A baseline's score therefore describes its rule on the windows it was run on, and the failures above show up only on the windows where they happen.

Naive and seasonal naive come from statsforecast (2.1.1). Its classes `Naive` and `SeasonalNaive` are in `statsforecast/models.py`. The seasonal naive rule is the one [Hyndman and Athanasopoulos](https://otexts.com/fpp3/toolbox.html#sec-simple-methods) give for seasonal data: the forecast is the last observed value from the same season. Average of weeks is not a library method, so `examples/lib/baselines.py` computes it in pandas, where the rule can be read. Each window reads only its own history, and a lag missing from that history raises an error instead of being skipped.

Example `naive-baselines-held-out-week` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.2:

```python
"""Score the three baselines for the lead client over the held-out week: naive, seasonal naive, average of weeks."""
import pandas as pd

from lib.backtest import held_out_cutoffs, score_windows, window_mae
from lib.baselines import BASELINES, baseline_forecasts
from lib.electricity import load
from lib.settings import LEAD, show

cutoffs = held_out_cutoffs()
df = load([LEAD])[["unique_id", "ds", "y"]]
forecasts = baseline_forecasts(df, cutoffs)
labels = ["naive", "seasonal naive", "average of weeks"]

show("windows", len(cutoffs))
show("scored hours", len(forecasts))
show("missing forecasts", int(forecasts[BASELINES].isna().sum().sum()))
show("mean demand", df[df["ds"].isin(forecasts["ds"])]["y"].mean())
for model, label in zip(BASELINES, labels):
    show(f"{label} MAE", score_windows(df, forecasts, model)["mae"])
for model, label in zip(BASELINES, labels):
    per_window = window_mae(df, forecasts, model)
    show(f"{label} worst window MAE", per_window.max())
    show(f"{label} worst window", per_window.idxmax().strftime("%b %d, %Y"))
    for day in ["2014-12-25", "2014-12-26"]:
        show(f"{label} MAE {pd.Timestamp(day):%b %d} window", per_window[pd.Timestamp(day)])
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

The example prints 7 windows and 168 scored hours, one for each hour of the seven days. The lead client's mean demand over those hours is 46.62 kWh. Every error in this section should be read against that level. It also prints 0 missing forecasts. The [working rule in the first section](#why-a-baseline-comes-first) asks for that count, and zero is the only value that lets the three scores be compared on the same hours.

The mean absolute error, MAE, is the mean of the absolute differences between forecast and reading, in kWh. The three baselines score:

- naive: 8.16 kWh
- seasonal naive: 8.36 kWh
- average of weeks: 8.96 kWh

The simplest rule has the lowest error on this week. Seasonal naive, which copies the whole previous day, is 8.36 kWh, and average of weeks, which averages four weeks, is the weakest at 8.96 kWh. The reason is not shown here, and the example does not claim one. The result is a single week of one client, and Chapter 3 is where the book backtests seasonal naive across many cutoffs.

The totals hide where the errors sit, so read the holiday window as well. The held-out week begins on Dec 25, 2014, a Portuguese national holiday, so its first window is not an ordinary day. Naive has the lowest error on that window, at 5.84 kWh, against 9.41 kWh for seasonal naive and 22.09 kWh for average of weeks. Average of weeks has its largest error of the week on that window, at 22.09 kWh, because its four lags are ordinary days and the holiday has no match among them. Seasonal naive has its largest error of the week on Dec 26, 2014, at 12.16 kWh, because that window copies the holiday's pattern. On that day naive is still lower, at 10.36 kWh. We recommend reporting all three baselines every time. Use seasonal naive as the main reference for MASE, because it carries the daily cycle that makes hourly demand predictable, and keep naive beside it, because on some weeks the flat rule is the stronger one.

**Working rule:** Start from naive and seasonal naive, both from the library, and add average of weeks when the series has a weekly rhythm worth testing. Before you trust a baseline, check one forecast by hand against its formula: pick one cutoff, compute one hour from the readings in its history, and compare the result with the forecast.

## Scale errors with MASE {#scale-errors-with-mase}

An MAE is in kWh, and a kilowatt-hour error means different things for different clients. An error of 8.36 kWh an hour is a small miss for a client that uses 46.62 kWh an hour. For a hypothetical client that uses 4 kWh an hour, the same error would be a large one. A scaled error removes that difference. It divides each absolute error by a scale, which is the typical error of a simple method on the same client's own history. The mean of the scaled errors is MASE, the mean absolute scaled error. [Hyndman and Koehler](https://robjhyndman.com/papers/mase.pdf) introduced it in a 2006 paper in the *International Journal of Forecasting*. The link is the authors' preprint, dated 2005. They noted that the scaled error does not depend on the units of the data, so the same number can be read across clients of very different size. This chapter scores one client, so that comparison across clients is the reason for the scale, not a result shown here.

The 2006 paper scales by the one-step naive error: the mean of the absolute difference between each reading and the reading before it. That is the natural scale for non-seasonal series. For hourly demand, this book uses the seasonal form that [Hyndman and Athanasopoulos](https://otexts.com/fpp3/toolbox.html#sec-accuracy) give for seasonal data. The reason is the comparison the reader wants. Under the seasonal scale, the denominator is the error that seasonal naive makes on the client's own history, so a MASE below 1 says that the forecast's error on the scored hours is smaller than the error seasonal naive made on that history. A one-step scale would compare the forecast with a method this book does not use for hourly demand.

The two formulas are these:

- `scale = mean of |y(t) - y(t - 24)|` over every reading t before the first test day, with the pairs that touch a masked clock-change hour left out
- `MASE = mean of |actual(t) - forecast(t)| / scale` over the scored hours

The scale reads every reading before the first test day, which is 17352 hours, about two years. That is longer than each window's eight-week history. A longer history gives a steadier estimate of the client's usual swing, and one scale for the week means every window of the week is read against the same number. The function `seasonal_scale` in `examples/lib/baselines.py` computes it for one client or for many, and returns one value per client.

The next example puts the scale to work on the held-out week. It scores the three baselines with the scale from history and with the scale from the whole series, and both scales mask the clock-change readings.

Example `mase-scale-leak-check` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.2:

```python
"""Score the lead client's held-out week in MASE with a scale from history and with a scale from the whole series.

Both scales have the clock-change readings masked, so the only difference between them is the test week.
"""
import pandas as pd

from lib.backtest import held_out_cutoffs
from lib.baselines import BASELINES, baseline_forecasts, mase_scores, scale_history, seasonal_scale
from lib.electricity import load
from lib.quirks import mask_clock_changes
from lib.settings import HELD_OUT_WEEK, LEAD, show

LABELS = ["naive", "seasonal naive", "average of weeks"]
first_day = pd.Timestamp(HELD_OUT_WEEK[0])

full = load([LEAD])
df = full[["unique_id", "ds", "y"]]
forecasts = baseline_forecasts(df, held_out_cutoffs())
history = scale_history(full, first_day)
masked_history = mask_clock_changes(history)
masked_whole = mask_clock_changes(full)
test_rows = len(full[full["ds"] >= first_day])

show("scale rows from history", len(history))
show("last scale reading from history", history["ds"].max().strftime("%b %d, %Y %H:%M"))
show("scale rows from whole series", len(full))
show("last reading of whole series", full["ds"].max().strftime("%b %d, %Y %H:%M"))
show("test week share of whole-series rows in percent", 100 * test_rows / len(full), digits=3)
show("clock-change rows in scale history", int(history["quirk"].ne("normal").sum()))
show("test week own mean day-to-day difference", seasonal_scale(full[full["ds"] >= first_day - pd.Timedelta(hours=24)]).loc[LEAD], digits=4)
show("scale from history as recorded", seasonal_scale(history).loc[LEAD], digits=4)
show("scale from history clock changes masked", seasonal_scale(masked_history).loc[LEAD], digits=4)
show("scale from whole series clock changes masked", seasonal_scale(masked_whole).loc[LEAD], digits=4)

hist = mase_scores(df, forecasts, BASELINES, masked_history).loc[LEAD]
whole = mase_scores(df, forecasts, BASELINES, masked_whole).loc[LEAD]
for model, label in zip(BASELINES, LABELS):
    show(f"{label} MASE from history scale", hist[model])
    show(f"{label} MASE from whole-series scale", whole[model])
    show(f"{label} MASE ratio whole-series over history", whole[model] / hist[model], digits=4)
show("seasonal naive MASE from history scale at four decimals", hist["SeasonalNaive"], digits=4)
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

The example takes the lead client's scale from its readings before the held-out week and prints it. The scale is in kilowatt hours too, so it reads against the client's mean demand the same way an MAE does. A scale that is a large share of the mean says the client's own day-to-day swing is large, and every error for that client is read against that swing. The scale is 7.1005 kWh, the average of the differences between each hour and the same hour the day before. Divide seasonal naive's MAE of 8.36 kWh by that scale and the result is its MASE, 1.18. The example takes this MASE from utilsforecast's `mase`, and it matches the division by hand.

utilsforecast (0.2.17) computes MASE with its `mase` function in `utilsforecast/losses.py`. The function takes its scale from the `train_df` it is given. It shifts that frame by rows, not by time, so a missing hour moves every later lag and nothing reports it. It also needs sorted input. Its time filter runs only when the scored frame has a `cutoff` column (function `_create_train_with_cutoffs`). So the library does not decide which readings the scale may read. The caller does, and the next section is about that choice.

**Working rule:** Report MASE beside MAE whenever the clients you compare differ in size, and say in the same sentence which history the scale comes from. Read MASE as a ratio of two mean errors, one from the scored hours and one from the history. It is not a percentage gain over seasonal naive, even when the MASE is well below 1.

## Take the MASE scale from history {#take-the-mase-scale-from-history}

A scale describes the history before the first test day, not the series as a whole. If the scale reads the whole series, it also reads the hours the forecast is scored on. The test week then enters the denominator of its own error. That is a leak, and it does not raise an error. The MASE it produces looks like any other MASE. The rule in this book is that a scale reads only the readings before the first test day of the week it scores. For the held-out week, that day is Dec 25, 2014.

A whole-series scale looks like the safer choice, because it uses more readings. It uses more readings from the wrong period. The extra readings are the ones the forecast is judged on, so the scale is no longer a measure of what was known at the cutoff. More data does not fix that. Only the cut does.

The [example in the previous section](#scale-errors-with-mase) builds both scales for the lead client and prints the rows each one reads. The history scale reads 17352 readings, and its last reading is Dec 24, 2014 23:00, the hour before the first test day. That line is the check. A reader who sees a later date there knows the test hours reached the scale. The whole-series scale reads 17520 readings, through Dec 31, 2014 23:00, which covers the whole held-out week. Both scales in this example have their clock-change readings masked, so the only difference between them is the test week.

The two scales are 7.1005 kWh from history and 7.1126 kWh from the whole series. The whole-series scale is larger, so every MASE computed with it is smaller, by the same factor for all three rules. The ratio is 0.9983 for naive, 0.9983 for seasonal naive and 0.9983 for average of weeks. At two decimals the leak does not show on this week. Seasonal naive's MASE is 1.18 with the history scale and 1.18 with the whole series. At four decimals the difference is visible: 1.1775 against 1.1755. The factor is the lesson, and the rounding is not.

Why is the effect so small? The test week is 0.959 percent of the whole-series readings. The whole-series scale is roughly the history scale moved toward the test week's own swing, by that share. The test week's own mean day-to-day difference is 8.3607 kWh, against 7.1005 kWh for the history, so the week swings more than the history does. The share times that gap is the leak, and the ratio above is its size. The leak therefore grows in two ways. It grows when more of the scale's rows are test hours, as in a test period much longer than one week, such as the year of cutoffs in Chapter 3. It also grows when the test week's swing sits further from the history's. A quieter week would pull the whole-series scale down and make every MASE larger, so the same leak can flatter a model in one week and penalise it in another.

The clock changes are a second, smaller point, and this chapter handles them as Chapter 3 does. The history holds 4 clock-change readings: the two gap hours and the two repeat hours of the March and October changes in 2013 and 2014. The gap hours read zero, and the repeat hours hold two hours of energy under one label, as the [data card](https://github.com/rollingedition/book-time-series-forecasting/blob/953a258e81dbd2d9435cf15185da38a7d3a7a49c/examples/data/README.md) describes. The scale keeps those pairs as recorded at 7.1121 kWh, and it leaves out the pairs that touch them at 7.1005 kWh. A masked reading is neither zero nor a copy. It is missing, so the pairs that touch it drop out of the mean. The chapter's scale therefore masks them. [Chapter 3 gives the reason](#meet-the-clock-changes), and it sets them to missing in every training set and every score.

**Working rule:** Pass a scale only the readings before the first test day, mask its clock-change readings, and print the last reading it uses. Check that this reading is the hour before the first test day. A small difference between the two scales does not show the procedure is right. The row check does.

## Read a baseline's score {#read-a-baselines-score}

MASE compares a forecast with seasonal naive's error on the client's own history. Below 1, the forecast's error on the scored hours is smaller than the error seasonal naive made on that history. Above 1, it is larger. [Hyndman and Koehler](https://robjhyndman.com/papers/mase.pdf) state this reading in their paper for the one-step scale, and the arithmetic is the same for the seasonal scale. The book gives no threshold for a good score. What counts as good depends on what a miss costs the supplier, which the supplier knows and this book does not.

The table puts the three baselines side by side. Each row is one baseline and each column is one measure. The MAE is in kWh, and the MASE uses the history scale with the clock changes masked. The leak from the previous section does not show at two decimals, so the table has one MASE column.

| Baseline | MAE (kWh) | MASE |
| --- | --- | --- |
| Naive | 8.16 | 1.15 |
| Seasonal naive | 8.36 | 1.18 |
| Average of weeks | 8.96 | 1.26 |

All three MASE values are above 1 on this week. So each baseline's error on the held-out week is larger than seasonal naive's typical error on the history. For seasonal naive itself, that means the week's day-to-day swing was larger than the history's. Its MAE equals the test week's own day-to-day differences, 8.3607 kWh, against 7.1005 kWh for the history. For naive and average of weeks, the scale compares them with seasonal naive, not with their own past, so this table does not say how those two rules did on the history. The week opens on a national holiday. The [earlier section](#three-baselines-to-beat) shows the holiday window as the largest error for average of weeks, and the book does not test the remaining days here.

The order is the same on both measures: naive first, seasonal naive second and average of weeks third. With one client that agreement is not a finding. MASE divides every MAE by the same scale, so the order cannot differ between MAE and MASE for one client. A model in the next chapters counts as better only when it beats the best baseline on more than one set of windows. One client and one week cannot establish that order for other clients or other weeks, and the comparison across clients is what the scale is for. Chapter 3 widens the test for seasonal naive to a year of cutoffs.

The table also answers a question the supplier will ask: is the simplest rule good enough to buy on? That depends on what an hour of error costs, and the MASE does not price it. What the MASE gives the supplier is a comparison it can repeat. A later model can be scored with the same helpers, so its MASE can be set beside these rows without a change of units.

Read the table in this order. First, confirm from the [earlier example](#three-baselines-to-beat) that every row scores the same hours, with no missing forecasts. Second, read the MASE column against 1. Third, compare each row with the others, not with a number from a textbook. A fitted model that is only as good as the best row has not shown much, and one that is better by less than the printed rounding has not shown anything at all.

**Working rule:** Read each baseline's MASE against 1 and against the other baselines, and do not name a winner on one week. A model counts as better only when it beats the best baseline on more than one set of windows, and when the margin is larger than the rounding of the printed scores.

## What goes wrong in production {#what-goes-wrong-ch2}

The first failure is a baseline that is not like-for-like. A team may score its model on a year of cutoffs and its baseline on one week, or give the model a longer history than the baseline. The comparison then measures the setup, and the printed numbers look like evidence. The check is the one this chapter uses. Every method takes its cutoffs from `held_out_cutoffs` and its history from `history_before`, and the count of missing forecasts is printed for each run.

The second failure is the leak in the scale. A scale that reads the test hours raises no error, and its MASE looks like any other. In this chapter the leak multiplies every seasonal naive MASE by 0.9983, a change that two decimals hide. A larger leak in another week would look the same on the page. The check is the printed row count and the last reading the scale uses. Both are one line of output, and a reviewer can read them without rerunning anything.

The third failure is a gap in the seasonal lag. With a missing hour, a lag of 24 rows reaches 25 hours back, so each pair for the next day compares the wrong hours, and the scale is wrong without any message. The library's `mase` has no gap check of its own. The helper `seasonal_scale` checks that each client's hours are unbroken, and `mase_scores` runs the same check on the scale's rows before the library reads them. The check raises an error rather than using an assertion, because Python removes assertions under `-O`. The scored hours are checked only for a reading and for duplicates. A production run should count the hours in the feed before it computes any scale, because a check that runs only inside the helper reports the problem after the damage is already in the scale.

The fourth failure is a seasonal lag chosen for the wrong cycle. A lag of 24 suits hourly demand with a daily cycle. Daily data has a weekly cycle, and hourly data with a weekly rhythm may need a lag of 168 instead. A scale computed with the wrong season is still a number, so nothing in the output shows the mistake. The check is to name the season beside the scale in the prose and to confirm it against the data's cycle before the scale is used.

The fifth failure is tuning a baseline on the test week. Average of weeks has a choice in it: how many weeks to average. If that number is picked because it gives the best score on the held-out week, the baseline has been fitted to the week it is judged on, and the comparison with the models is no longer fair. This book fixed four weeks before any score was printed, and this chapter keeps it for every window. A change to it belongs in the decision list at the end of the chapter, made before the scores are seen.

**Working rule:** Before you trust a baseline or a scale, check its inputs in this order: the same windows for every method, a scale that reads only earlier readings with its last reading printed, an unbroken hourly history for the seasonal lag, and a season that matches the data's cycle. Each check is one line of output or one count, and a failed check stops the comparison until it is fixed.

## Decisions this chapter made {#decisions-ch2}

This chapter made seven choices, and the hand-off to Chapter 3 is the last of them. Most are in `examples/lib/baselines.py`, so a later edition that changes one changes it everywhere it is used. The history length and the horizon are the settings in `examples/lib/settings.py`, the same ones Chapter 1 used, so no baseline here reads a different history from the forecasts beside it.

- The MASE scale is seasonal, with a lag of 24 hours. The one-step scale of the 2006 paper is not used.
- The scale is one number per client for the held-out week, from every reading before Dec 25, 2014. It is longer than each window's history, as set out above. utilsforecast can take a scale per cutoff when the frame carries a cutoff column, but this chapter does not use that option. If you add one, know that its filter keeps `ds <= cutoff`, so the cutoff hour itself is included. A cutoff in this book is the first hour a forecast covers, and its reading is not history. A cutoff column built from this book's cutoffs must therefore be shifted back one hour first.
- Average of weeks uses the four weeks before each forecast day, is computed in pandas, and reads only its own eight-week history.
- Naive and seasonal naive are the statsforecast classes. Scores are pooled over the 168 scored hours and printed to two decimals.
- The scale masks its 4 clock-change readings, following Chapter 3's rule. The printed history scale is then 7.1005 kWh.
- The baselines draw no random numbers, so the examples set no seed.
- Chapter 3 keeps seasonal naive and these helpers, runs it over a year of Sunday cutoffs, and reads one scale per client from every reading before the first cutoff, the rule this chapter sets out. That is the test one week cannot provide.
