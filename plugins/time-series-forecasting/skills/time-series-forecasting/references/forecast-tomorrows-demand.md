---
title: "Time Series Forecasting"
chapter: "Forecast tomorrow's demand"
chapter_id: forecast-tomorrows-demand
book: time-series-forecasting
edition: 2026.11.2
verified: 2026-11-11
edition_code: RHYP-H8RM
canonical: https://rollingedition.com/time-series-forecasting/forecast-tomorrows-demand
license: CC BY 4.0
attribution: "“Forecast tomorrow's demand,” chapter 1 of Time Series Forecasting, Edition 2026.11.2, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/forecast-tomorrows-demand. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Forecast tomorrow's demand

By the end of this chapter you can load one client's hourly demand, forecast its next day with a seasonal naive baseline and with one statistical model, and score both forecasts on the same 7 days. The result is rough on purpose. It has no ranges, no tuning and one client to judge by. Each later chapter makes one part of it solid. You need Python, pandas, and the mean of a sample and what an error is. Nothing else is assumed. The core terms are defined in a line where they first appear.

## The case and its data {#the-case-and-its-data}

This book follows one case: an electricity supplier that buys power a day ahead for its clients. We call it the supplier.

The supplier commits to its purchases before the day starts. For each hour of the next day it needs to know how much its clients will use, and it needs a range as well as a single number, because buying too little costs more than buying too much. This book builds the forecast that such a purchase starts from. A forecast here is the expected demand of one client in each hour, made from readings recorded before the forecast was made.

Three terms fix what a forecast is. The moment a forecast is made is its cutoff. It uses only the readings before that cutoff, and it reaches forward a fixed number of hours, its horizon. A window is one cutoff with its horizon and the forecast it produces. Here the horizon is 24 hours, so each window covers one day: the 24 hours that start at its cutoff.

The timing matters as much as the method. Every window in this book has its cutoff at 00:00 on the day it predicts, so the last reading it can use is the one for 23:00 on the day before. The case buys before the day starts, so a midnight cutoff is a simplification. The book keeps it so that each window needs only the day before. A supplier that buys earlier would cut earlier and forecast further ahead. A forecast that reads one hour past its cutoff would use information the supplier does not have when it buys, and its score would flatter it.

The data is public. It is the ElectricityLoadDiagrams20112014 dataset from the UCI Machine Learning Repository, by Trindade (2015), with the DOI 10.24432/C58C86. It is licensed under CC BY 4.0. The book ships a cut of it, `electricity_hourly.csv.gz`, with the licence beside it in the same folder. The [data card](https://github.com/rollingedition/book-time-series-forecasting/blob/953a258e81dbd2d9435cf15185da38a7d3a7a49c/examples/data/README.md) gives the source, the cut and its limits.

The raw file holds 370 clients, with a reading every 15 minutes. The cut averages the four readings of each hour, which gives the energy used in that hour in kWh, and it keeps two whole years, 2013 and 2014. One client, `MT_223`, has no non-zero reading in that window, so the cut drops it. The 369 clients that remain are sorted by id, and 30 are kept at evenly spaced positions. A reader who cuts the raw file must drop `MT_223` and take the same 30 evenly spaced positions, or the counts in this book will not match.

The clients have anonymous ids such as `MT_014`. The dataset does not say what they are, so the book calls them clients. It does not describe them as companies or households.

Two groups of clients recur through the book. The thirty clients are every client in the cut. The 8 clients of `SUBSET8` are every fourth client of the thirty, starting with the second. Later chapters use that subset where a full run would take too long, and it includes one client that starts late. The lead client, `MT_014`, is the first client of `SUBSET8`. This chapter and its single-client examples use it.

The test period is the last week of 2014, from Dec 25 to Dec 31, 2014. The forecasts in this chapter are scored on it, and it is called the held-out week. Each forecast uses only readings from before its cutoff, so no forecast learns from the day it predicts. The week is not quiet. Dec 25, 2014 is Christmas Day, a national holiday in Portugal, where the data's clock is set. This chapter scores the week as it is, and the scores show what the holiday does. Chapter 5 tests a holiday flag on holiday windows and does not keep it, so the book does not repair the holiday here. Chapter 10 shows its cost.

A forecast says what demand is likely to be. It does not say why. The data records how much each client used. It cannot say what demand would have been under a different price or contract. That is a causal question, and it needs a different design.

**Working rule:** Check the cut against the data card before any forecast is made. The file should hold 30 clients, and the example counts how many of them have a full two years of hourly rows. Those counts should match the card. Confirm that `MT_223` is missing and explained. A cut that does not match the card is different data, and every number computed from it describes that data, not this one.

## Load one client's hourly demand {#load-one-clients-demand}

A time series is a sequence of readings in time order. In the book's file, each row is one client in one hour, and each client's hours are in time order. To load one client, keep that client's rows. The helper `load` in `examples/lib/electricity.py` does that and returns four columns. `unique_id` names the client. `ds` is the hour. `y` is the energy used in that hour, in kWh. `quirk` tells you whether the row needs special handling.

The `ds` column is the start of the hour, in local clock time with no time zone. The data card gives this label, and the book's examples treat the index as one naive hourly index. Each row's `quirk` is one of four labels:

- `normal` is an ordinary hour.
- `before_first_reading` is an hour before a client's first non-zero reading. Only a late-starting client has these rows.
- `clock_change_gap` is 01:00 on a March clock-change day. The dataset's note says it reads zero for every client. The data card measures it: of 57 such hours with non-zero neighbours, 55 read below 5% of them.
- `clock_change_repeat` is 01:00 on an October clock-change day. It holds about two hours of energy under one label.

The book keeps every value as the meter recorded it. Nothing is filled, smoothed, removed or rescaled. A zero in a gap hour and a doubled October hour are therefore still in the file, flagged but not corrected. Chapter 3 decides what each flagged row means for a model. This chapter only needs to know the labels exist, and to check that none of them falls inside the windows it scores.

The lead client has readings in every hour of the window, so none of its rows are `before_first_reading`. Over the two years it has 17516 ordinary rows. It has 2 gap rows and 2 repeat rows, one of each in each year.

Example `load-lead-client` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · utilsforecast 0.2.17), passing in Edition 2026.11.2:

```python
"""Load the lead client's hourly demand, count its quirks, and check the held-out histories."""
from lib.backtest import held_out_cutoffs, history_before
from lib.electricity import load
from lib.settings import LEAD, show


def fmt(ts):
    return ts.strftime("%Y-%m-%d %H:%M")


FULL_ROWS = 2 * 365 * 24  # two years of hours; 2013 and 2014 are not leap years

everyone = load()
show("clients in the file", everyone["unique_id"].nunique())
show(f"clients with {FULL_ROWS} rows", int((everyone.groupby("unique_id").size() == FULL_ROWS).sum()))

df = load([LEAD])
show("rows", len(df))
show("first reading", fmt(df["ds"].min()))
show("last reading", fmt(df["ds"].max()))
for quirk in ["normal", "before_first_reading", "clock_change_gap", "clock_change_repeat"]:
    show(f"{quirk} rows", int((df["quirk"] == quirk).sum()))

windows = [history_before(df, cutoff) for cutoff in held_out_cutoffs()]
show("history rows per window", min(len(w) for w in windows))
show("longest history rows", max(len(w) for w in windows))
show("first history reading", fmt(windows[0]["ds"].min()))
show("clock-change rows in held-out histories",
     sum(int(w["quirk"].isin(["clock_change_gap", "clock_change_repeat"]).sum()) for w in windows))
```

Output:

```text
clients in the file: 30
clients with 17520 rows: 30
rows: 17520
first reading: 2013-01-01 00:00
last reading: 2014-12-31 23:00
normal rows: 17516
before_first_reading rows: 0
clock_change_gap rows: 2
clock_change_repeat rows: 2
history rows per window: 1344
longest history rows: 1344
first history reading: 2014-10-30 00:00
clock-change rows in held-out histories: 0
```

The example prints those counts, the first and last readings, and a check on the histories that this chapter's forecasts use. The file holds 30 clients. The lead client has 17520 rows, from 2013-01-01 00:00 to 2014-12-31 23:00.

Counting rows is the first check. Two years of hours is 17520 rows for each client, and the example counts the clients that have exactly that many: 30 of 30. So no hour is missing from the file for those clients. A window with fewer hours than its history should hold has a gap, and the gap would be the first thing to explain. Check the client count and the row count against the card.

A forecast needs history. The book's history is 8 weeks, which is 1344 hours, and each cutoff in the held-out week gets exactly that much before it. The shortest history has 1344 rows, and the longest has 1344. For the first cutoff of the held-out week, the history begins at 2014-10-30 00:00. That is after the clock change of Oct 26, 2014, which the data card dates. So none of the 7 histories holds a clock-change hour, and the example counts 0 clock-change rows across them.

The rest of this chapter can leave the clock-change rows alone for that reason. Chapter 3 meets them, and Chapter 4 meets the late starter.

**Working rule:** Choose the client and the window first, then count the quirks in that window's history before any model sees it. If a history holds a clock-change label or a `before_first_reading` row, do not hand it to a model unchanged, because the model will read the label's value as demand. Chapter 3 and Chapter 4 give the rules for those rows. A window that holds neither can use its rows as they are, as this chapter does.

## Forecast the next day with seasonal naive {#forecast-with-seasonal-naive}

The first forecast is the simplest one to make, and every later forecast has to beat it. It uses the case's cutoff and horizon from [the case and its data](#the-case-and-its-data), and the history that [loading one client](#load-one-clients-demand) describes. Seasonal naive says that each future value equals the last observed value from the same season. Hyndman and Athanasopoulos define it for a season of any length `m`. The forecast for a future value is the value observed one season earlier ([Hyndman and Athanasopoulos, *Forecasting: Principles and Practice*, ch. 5](https://otexts.com/fpp3/toolbox.html#sec-accuracy)). With hourly data and a daily cycle, the season is 24 hours. The forecast for an hour of tomorrow is then the reading at the same hour today. In the notation of this book, the forecast for hour `t` is `y(t - 24)`.

Nothing in this rule is fitted. The forecast is a copy of the data, so it needs no estimation step. It never reads ahead of its cutoff, whichever cutoff it is. For each hour from the cutoff to 23 hours after it, `t - 24` falls between 24 hours before the cutoff and the hour before it, so the copy uses only history.

The held-out week has 7 windows, one for each day from Dec 25 to Dec 31, 2014, each made at 00:00. The supplier's question is tomorrow's demand for `MT_014`. For Dec 25, the forecast copies the readings of Dec 24 at each hour. The same rule gives the forecast for every other day of the week, using only the day before.

Take the window at 00:00 on Dec 25 as a worked case. Its forecast for 00:00 on Dec 25 is the reading at 00:00 on Dec 24, and its forecast for 23:00 on Dec 25 is the reading at 23:00 on Dec 24. Of the 1344 hours in its history, this method uses only the last 24, because statsforecast's `_seasonal_naive` repeats the last season of values (statsforecast 2.1.1, `statsforecast/utils.py`). The example still passes all of them, because the same call serves the models that do use more of the history, and a reader who sees one call with one history length does not have to learn a second form later.

Why a day and not a week? A season of 168 hours would copy the same hour of the same weekday from the week before, which is another valid baseline for a series with a weekly rhythm. This chapter uses the daily season because the question is the next day, and because the day-ahead forecast is the one the case needs.

Example `seasonal-naive-next-day` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.2:

```python
"""Forecast the lead client's next day with seasonal naive for each day of the held-out week, and score it."""
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows, held_out_cutoffs, scoring_counts, score_windows, window_mae
from lib.electricity import load
from lib.settings import HORIZON, LEAD, show


def day_mean(day):
    return df[df["ds"].dt.normalize() == pd.Timestamp(day)]["y"].mean()


df = load([LEAD])[["unique_id", "ds", "y"]]
sf = StatsForecast(models=[SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df, held_out_cutoffs())
scores = score_windows(df, forecasts, "SeasonalNaive")
counts = scoring_counts(df, forecasts, "SeasonalNaive")

show("horizon hours", HORIZON)
show("windows", counts["windows"])
show("scored hours", counts["scored_hours"])
show("missing forecasts", counts["missing_forecasts"])
show("mean demand", df[df["ds"].isin(forecasts["ds"])]["y"].mean())
show("mean demand 2014-12-24", day_mean("2014-12-24"))
show("mean demand 2014-12-25", day_mean("2014-12-25"))
show("MAE", scores["mae"])
show("RMSE", scores["rmse"])
for day, mae_day in window_mae(df, forecasts, "SeasonalNaive").items():
    show(f"MAE {day:%Y-%m-%d}", mae_day)

# The check is run on a history with one hour removed, to show it refuses a short history.
cutoff = held_out_cutoffs()[0]
gap = df[df["ds"] != cutoff - pd.Timedelta(hours=1)]
try:
    forecast_windows(sf, gap, [cutoff])
    refused = "no"
except ValueError:
    refused = "yes"
show("history with one hour removed refused", refused)
```

Output:

```text
horizon hours: 24
windows: 7
scored hours: 168
missing forecasts: 0
mean demand: 46.62
mean demand 2014-12-24: 47.58
mean demand 2014-12-25: 38.40
MAE: 8.36
RMSE: 10.87
MAE 2014-12-25: 9.41
MAE 2014-12-26: 12.16
MAE 2014-12-27: 5.10
MAE 2014-12-28: 11.16
MAE 2014-12-29: 8.68
MAE 2014-12-30: 5.26
MAE 2014-12-31: 6.75
history with one hour removed refused: yes
```

The example builds the windows. For each one it takes the 1344 hours before the cutoff, makes the forecast, checks it, and scores it against the readings that followed. It prints 7 windows, 168 scored hours, one for each hour of the 7 days, and 0 missing forecasts. It also prints the mean demand over those hours, 46.62 kWh. That mean is the level against which every error in this chapter should be read.

Seasonal naive is a baseline, and when a daily cycle dominates the series it can be a strong one. Its weakness is that it copies a single day. An unusual day becomes the forecast for the next, and the method has no way to average it out.

**Working rule:** Keep seasonal naive in every comparison for an hourly series with a daily cycle. It needs no fitting, so it runs on every window at no extra cost. A model that cannot beat it on the same windows has not earned its extra work. Check the forecasts for missing values before you read their score, because a missing reading in the last season becomes a missing forecast. Chapter 3 gives the rule for filling those hours before any model runs.

## Forecast the next day with one model {#forecast-with-a-statistical-model}

This section uses the same 7 windows, and the baseline above is what it has to beat. A baseline answers what you get with no model at all. The question that follows is whether a fitted model does better on the same windows. The model here is AutoETS. The statsforecast source describes it as a model that "Automatically selects the best ETS (Error, Trend, Seasonality) model using an information criterion" (statsforecast 2.1.1, `statsforecast/models.py`, class `AutoETS`). The criterion is AICc, the Akaike information criterion corrected for small samples. It is set in `ets_f`, in `statsforecast/ets.py`, and `AutoETS` does not offer another (statsforecast 2.1.1, `statsforecast/ets.py`, function `ets_f`).

The `model` string sets which forms the model may take, with one letter each for error, trend and season. `Z` lets AICc choose, and `A` fixes the form to additive. This chapter uses `ZZA`: AICc chooses the error and the trend, and the season is additive, so every candidate has a daily cycle. The default, `ZZZ`, also lets AICc choose the season. On this client and these 7 cutoffs it chose no season in every window, a flat form, ETS(A,N,N), so its forecast is one value repeated for the day. This chapter asks whether a model with the daily cycle beats a copy of yesterday, so it does not use that form. Other seasonal forms score differently on this week, and Chapter 4 looks at the forms and the choice.

Each fit does three things, and each one matters for what the score means. At a cutoff, AutoETS reads the 1344 hours before it. It compares the candidate forms and keeps the one with the lowest AICc. AICc rewards a close fit to the history and charges for each parameter the form uses, so a form with more parameters must fit much better to win. Then the model projects that form 24 hours ahead. The held-out week therefore means 7 separate selections, not one. In this week 7 windows chose ETS(A,N,A): additive error, no trend and an additive daily season. The 7 fits still differ in their parameters. The book does not quote them, because each is a detail of one fit, and a reader should not take it as a finding.

The comparison is fair only when nothing else changes. The example uses the same 7 cutoffs and the same 1344 hours of history before each one. It refits the model at every cutoff, using only the history before that cutoff. Only the model differs from the baseline.

Example `autoets-next-day` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.2:

```python
"""Forecast the lead client's next day with AutoETS for each day of the held-out week, and score it."""
import numpy as np
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

from lib.backtest import chosen_forms, forecast_windows, held_out_cutoffs, scoring_counts, score_windows, window_mae
from lib.electricity import load
from lib.settings import HORIZON, LEAD, SEED, show

np.random.seed(SEED)
df = load([LEAD])[["unique_id", "ds", "y"]]
# model="ZZA": AICc chooses the error and trend forms; the seasonal form is fixed to additive, so every form has a day cycle.
sf = StatsForecast(models=[AutoETS(season_length=24, model="ZZA")], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df, held_out_cutoffs())
scores = score_windows(df, forecasts, "AutoETS")
counts = scoring_counts(df, forecasts, "AutoETS")
forms = chosen_forms(sf, df, held_out_cutoffs())

show("horizon hours", HORIZON)
show("windows", counts["windows"])
show("scored hours", counts["scored_hours"])
show("missing forecasts", counts["missing_forecasts"])
for form, n in forms.items():
    show(f"windows that chose {form}", n)
show("MAE", scores["mae"])
show("RMSE", scores["rmse"])
for day, mae_day in window_mae(df, forecasts, "AutoETS").items():
    show(f"MAE {day:%Y-%m-%d}", mae_day)
```

Output:

```text
horizon hours: 24
windows: 7
scored hours: 168
missing forecasts: 0
windows that chose ETS(A,N,A): 7
MAE: 8.86
RMSE: 10.91
MAE 2014-12-25: 13.51
MAE 2014-12-26: 11.21
MAE 2014-12-27: 4.17
MAE 2014-12-28: 10.03
MAE 2014-12-29: 9.53
MAE 2014-12-30: 6.33
MAE 2014-12-31: 7.25
```

The example prints the same window and hour counts as the seasonal naive example, and the number of windows that chose each form, so the two scores cover the same 168 hours. The scores appear in the next section, beside the baseline's. The question the model answers is whether a model that keeps the daily cycle predicts the next day better than a copy of yesterday. It has 7 fits to make that call, one at each cutoff, and each fit sees only what was known at its cutoff.

**Working rule:** Add a model only with a baseline it has to beat on the same windows. Refit the model at each cutoff, using history from before that cutoff only. A model fitted once on the whole series and then scored on that series has seen the answers, and its score is not a forecast score.

## Score both on a held-out week {#score-on-a-held-out-week}

Both examples have now made 7 day-ahead forecasts, from the two sections above. A score turns their errors into one number. The error of an hour is the actual demand minus the forecast. This chapter uses two scores. The mean absolute error, MAE, is the average size of the miss: `MAE = mean(abs(actual - forecast))`. The root mean squared error, RMSE, is `RMSE = sqrt(mean((actual - forecast)^2))`. Both are in kWh, and they answer different questions. Hyndman and Athanasopoulos note that a forecast minimising MAE is a forecast of the median, and one minimising RMSE is a forecast of the mean ([Hyndman and Athanasopoulos, ch. 5](https://otexts.com/fpp3/toolbox.html#sec-accuracy)). Because RMSE squares each error, a few large misses raise it more than they raise MAE.

Both scores come from utilsforecast (0.2.17). Its `mae` is the mean of the absolute errors, and its `rmse` is the square root of the mean of the squared errors (`utilsforecast/losses.py`, functions `mae` and `rmse`). The scores pool the 168 scored hours. Each hour counts once, and each of the 7 windows contributes 24 of them. The two models give these scores. Each row is one model and each column is one score. Both columns are in kWh, so each can be read against the mean demand. A lower number means forecasts closer to the readings.

| Model | MAE (kWh) | RMSE (kWh) |
| --- | --- | --- |
| SeasonalNaive | 8.36 | 10.87 |
| AutoETS | 8.86 | 10.91 |

Read those numbers against the mean demand of 46.62 kWh an hour. The baseline misses by 8.36 kWh an hour on average, and AutoETS by 8.86 kWh. For the supplier, the MAE is the typical miss to plan for in each hour. RMSE is always at least MAE. For normal errors RMSE is about 1.25 times MAE, so a ratio well above that means a few large misses. This section reads the two scores together and goes no further, because one client over one week cannot show the spread of the misses.

AutoETS is higher than the baseline on both scores: 8.86 against 8.36 on MAE, and 10.91 against 10.87 on RMSE. The daily lines show where the two differ. The baseline's worst day is Dec 26, the day after Christmas, when it copies Christmas Day: 12.16 kWh an hour, the largest of the 7. AutoETS's worst day is Dec 25 itself, at 13.51 kWh, against 9.41 for the baseline. On Dec 26 AutoETS misses by 11.21 kWh.

A gap of this size on one client over one week is not a verdict. 7 forecasts make a small sample, and a ranking built on one week can flip on the next. Chapter 3 backtests seasonal naive over a year of Sunday cutoffs.

The score also has to match the decision. The [case](#the-case-and-its-data) says that buying too little costs more than buying too much, so a miss in one direction does not cost the same as a miss of the same size in the other. MAE and RMSE treat the two directions alike, because they use the size of each miss and not its sign. That is enough for this chapter, which asks whether a forecast is close. It is not enough for the purchase. Chapter 8 builds ranges for that decision, and scores them against what happened.

**Working rule:** Score each model on forecasts it made without the scored hours in its history, over more than one day, and report the number of windows and hours behind each score. Compare models only on the same windows. Read MAE and RMSE together. If they disagree about which model is better, look at the largest misses in the windows before you choose, because a few large misses can decide the result.

## What goes wrong in production {#what-goes-wrong-ch1}

The forecasts and scores above can go wrong in 5 ways, and only some of them print an error. The [cutoff rule](#the-case-and-its-data) and the [seasonal naive rule](#forecast-with-seasonal-naive) say what each window must hold.

The first failure is a label that is off by an hour. If a reader takes `ds` as the end of its hour rather than the start, the forecasts and the readings they are scored against carry the same shift, so the score does not change. The error is in the purchase instead: the forecast would cover different hours from the ones the supplier buys for. No score in this chapter detects it. The data card fixes the label, and it is the first thing to check when a forecast is moved to new data.

The second failure is leakage. A window whose history includes the hours it predicts scores too well, and nothing in the score says so. [Hewamalage, Ackermann and Bergmeir (2022)](https://arxiv.org/abs/2203.10716) warn that rolling-origin evaluation is prone to this leak when it is not done with care. The checks here are the cutoff rule and the history length. Each history must end before its cutoff, and each must hold 1344 rows. `history_before` raises an error when a history is short or long. The example shows the refusal: a history with one hour removed is refused (yes).

The third failure is copying an unusual day. Seasonal naive copies yesterday, so an unusual day becomes tomorrow's forecast. The held-out week holds one. Dec 25, 2014 is Christmas Day, and the lead client's mean demand that day is 38.40 kWh an hour, against 47.58 kWh on Dec 24. The window for Dec 26 copies that day. It has the largest MAE of the 7 windows, 12.16 kWh, against 9.41 on Dec 25 and 5.10 on Dec 27. That is the failure, and the scores show it. One holiday is too few to measure a holiday effect. Chapter 5 tests a holiday flag on holiday windows and does not keep it, so the book does not repair the holiday here. Chapter 10 shows its cost.

The fourth failure is a missing reading. The statsforecast seasonal naive does not check its input. It repeats the last season's values, so a missing value in that season becomes a missing forecast (statsforecast 2.1.1, `statsforecast/utils.py`, function `_seasonal_naive`). The example prints the count of missing forecasts (0 here), because a hole in the forecast is an hour the score does not describe. Chapter 3 fills the hours that need filling, from data before the cutoff, before any model runs.

The fifth failure is a flattering window. A week with no unusual days can make almost any forecast look good, and a week with one can make every forecast look bad. The held-out week has a holiday in it, and it is still one week for one client. The score then describes the week more than the method. The fix is breadth: compare models on several windows of different kinds before you trust a ranking.

**Working rule:** Before you trust a score, check three things in this order: each window's first forecast hour is its cutoff, each history ends before its cutoff and holds the full history length, and no forecast is missing. The helpers raise an error for the first two, and the examples print the third. A score counts as a finding only after all three pass.

## Decisions this chapter made {#decisions-ch1}

This chapter made 9 choices. Most are settings in `examples/lib/settings.py`, so a later edition that changes one changes it in every chapter that uses it. The rest are stated in the data card or in this chapter. Chapter 2 starts from these two forecasts and their two scores, and asks whether either is good enough to act on.

- Each window's cutoff is at 00:00 on the day it predicts, and the horizon is 24 hours, so each window covers that day.
- The history before each cutoff is 1344 hours, which is 8 weeks.
- The lead client is `MT_014`. The held-out week is Dec 25 to Dec 31, 2014: 7 windows and 168 scored hours.
- The scores are MAE and RMSE, pooled over the 168 hours and printed to two decimals.
- The models are seasonal naive with a season of 24 hours, and AutoETS with the model string `ZZA` and a season of 24 hours. The examples run statsforecast with one job. Neither point forecast draws random numbers, so the seed the AutoETS example sets, by convention, has no effect on it.
- The cut drops `MT_223` and keeps 30 clients, as the data card explains.
- The clock-change and late-starter rows stay as they are, because no history in this chapter contains them. Chapter 3 and Chapter 4 handle them.
- Every number the prose quotes is bound to a labelled line in its example's recorded output, so the text and the output cannot disagree silently.
- The chapter builds one client's forecast and no ranges. Chapter 8 is where ranges begin.
