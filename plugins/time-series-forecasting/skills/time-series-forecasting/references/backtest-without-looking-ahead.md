---
title: "Time Series Forecasting"
chapter: "Backtest without looking ahead"
chapter_id: backtest-without-looking-ahead
book: time-series-forecasting
edition: 2026.11.1
verified: 2026-11-11
edition_code: HK8M-ENSS
canonical: https://rollingedition.com/time-series-forecasting/backtest-without-looking-ahead
license: CC BY 4.0
attribution: "“Backtest without looking ahead,” chapter 3 of Time Series Forecasting, Edition 2026.11.1, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/backtest-without-looking-ahead. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Backtest without looking ahead

By the end of this chapter you can score a day-ahead forecast over a year of cutoffs without letting the future into its history, handle the two clock-change hours in the data, and run a shift test that catches a feature which reads past its cutoff. You need what Chapter 2 gave you: the seasonal naive baseline, MAE, and a scale taken from history. The method stays the same. What changes is how many times you score it, and how carefully you cut the data each time.

## Why one test week misleads {#why-one-test-week-misleads}

The held-out week of Chapter 1 gives the supplier seven forecasts for one client, which is 168 scored hours. That sample is small enough to be lucky. A forecast can match a calm week and miss the next one, and a single week cannot tell you which happened. The supplier buys every day, so the question it needs answered is how the forecast does across many days, including the unusual ones.

A backtest answers that question with the data you already have. It makes a forecast at many past moments, each with only the readings available at that moment, and scores each one against the readings that followed. Each such moment is a cutoff. Each cutoff, with the hours it forecasts, is a window. The scores of all the windows together say how the method behaves across the year, not on one week.

This matters most for the clock changes. A year of cutoffs contains the March change, when the 01:00 hour does not occur on the clock, and the October change, when one 01:00 label holds two hours of energy. A single week, such as the last week of December, contains neither. A backtest that does not reach those dates cannot show what the method does on them, so the sample has to be chosen with them in mind.

**Working rule:** Prefer a year of cutoffs before you trust a difference between two methods. When cost forces fewer, say so beside each score, as Chapters 4 to 9 do. Make sure the sample reaches the odd days of the year. Report how many windows and how many scored hours stand behind each number. A figure from one week is one sample, and a reader should be able to see that.

## Roll the cutoff forward {#roll-the-cutoff-forward}

A window has three parts: the cutoff, the horizon and the history. The cutoff is the moment the forecast is made. The horizon is how far ahead it reaches, which is 24 hours here, so the forecast covers the 24 hours that start at the cutoff. The history is the readings before the cutoff that the model may use, which the book sets at 1,344 hours, or eight weeks. Move the cutoff by a step and you have the next window. The step is one week for the Sunday sample, and one day for the daily samples in the two clock-change subsections, [The March hour that reads zero](#the-march-hour-that-reads-zero) and [The October hour that holds two](#the-october-hour-that-holds-two).

In words, each window's targets are the 24 hours from its cutoff, and its history is the readings from 1,344 hours before the cutoff up to, but not including, the cutoff. The next window moves both by one step. A reading can therefore be a target in one window and history in a later one. That is correct, because by the later cutoff the reading lies in the past, and it is the same reading in both places.

The Sunday sample runs seasonal naive over every Sunday of 2014, from Jan 5 to Dec 28, 2014. The EU puts every clock change on the last Sunday of March and of October (Directive 2000/84/EC, Articles 2 and 3), and both changes of 2014, on Mar 30 and Oct 26, are in the sample. The sample uses the subset of eight clients, `SUBSET8`, which is every fourth client of the thirty, starting with the second. The example:

Example `backtest-sundays-2014` (Python 3.13.16 · holidays 0.108 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Seasonal naive over the 52 Sunday cutoffs of 2014 for the subset of eight clients, with no rule applied."""
import pandas as pd
from holidays import country_holidays
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows, history_before
from lib.electricity import load
from lib.quirks import year_scores
from lib.scoring import book_scale, clients_left_out
from lib.settings import HORIZON, SUBSET8, show

COLS = ["unique_id", "ds", "y"]
cutoffs = pd.date_range("2014-01-05", "2014-12-28", freq="W-SUN")  # 52 Sundays, both clock changes among them
df = load(SUBSET8)[COLS + ["quirk"]]
sf = StatsForecast(models=[SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df[COLS], cutoffs, h=HORIZON)
scored = forecasts.merge(df, on=["unique_id", "ds"])
scale = book_scale(df, cutoffs[0])  # the MASE scale: every reading before the first cutoff, from 2013 on
sizes = pd.concat([history_before(df, c).groupby("unique_id").size() for c in cutoffs])
holidays = country_holidays("PT", years=[2014])

show("windows", len(cutoffs))
show("history hours per series, min over windows", sizes.min())
show("history hours per series, max over windows", sizes.max())
show("Sunday windows on a Portuguese holiday", sum(c.date() in holidays for c in cutoffs))
show("client left out of MASE", ", ".join(clients_left_out(df, cutoffs[0])))
for label, value in year_scores(scored, scale).items():
    show(label, value)
```

Output:

```text
windows: 52
history hours per series, min over windows: 1344
history hours per series, max over windows: 1344
Sunday windows on a Portuguese holiday: 1
client left out of MASE: MT_115
scored hours: 9936
scored hours before a first reading: 48
MAE: 382.02
RMSE: 1369.57
largest client by absolute error: MT_370
largest client's share of absolute error, percent: 88.69
clients in MASE: 7
mean MASE: 0.97
lowest client MASE: 0.77
highest client MASE: 1.26
```

The example prints 52 windows and 9936 scored hours. That is eight clients times 24 hours times the windows, less the hours of one late starter before its first reading, which the next paragraphs explain. Each window's history holds 1344 to 1344 hours for each client. That is the eight weeks the book specifies, in every window, and the example prints both ends to show it.

The headline is per-client MASE, not the pooled error. The MASE scale is one number per client, and `scoring.book_scale` computes it for the whole book: every reading before the first cutoff, with the clock-change hours masked and each client's leading zeros removed. The first cutoff is Jan 5, 2014, so this sample's scale is read from Jan 1, 2013 to Jan 4, 2014. The mean of the per-client MASE values is 0.97, with the lowest at 0.77 and the highest at 1.26, over 7 clients. The pooled MAE is the second line: 382.02 kWh over the scored hours. It compares methods on the same clients and windows, but it cannot compare clients with each other. Its largest client, MT_370, carries 88.69 percent of the absolute error, because that client uses thousands of kilowatt hours an hour, so its errors are in the thousands too. The RMSE is 1369.57 kWh.

Client MT_115 has no reading before Jan 14, 2014. Until then the meter reports zeros, and the data card says those zeros are not demand. The example leaves the 48 hours before its first reading out of every score, which are the first two windows. Its history still holds those zeros, because the start rule for histories belongs to Chapter 4. Its MASE is left out for a different reason: its scale is read from the readings before Jan 5, 2014, and it has none. The example reports that client as left out of MASE, and Chapter 4 meets its start.

The statsforecast library has a function for this loop, `cross_validation`, and it is possible to call it without the window you wanted. At version 2.1.1, the training slice of each window starts at the first reading of the series unless you pass `input_size`. The history then grows from one window to the next, and the eight-week rule is not in force. Hyndman and Athanasopoulos state the principle that the training set consists only of observations before the test set (*Forecasting: Principles and Practice*, 3rd ed., chapter 5). The code behind `cross_validation` decides the length of that set (statsforecast 2.1.1, `statsforecast/core.py`). Its cutoff is the last hour a window trains on, where this chapter's cutoff is the first hour it forecasts, so the two names differ by one hour. This chapter builds each window's history itself, from the cutoff backwards. That gives the same 1,344 hours at every window and makes the rule visible in the code.

**Working rule:** Set the history length explicitly, in hours, and check that it is the same for every window. When a library loops over windows for you, read how it sets the training slice before you trust its output, because its default may be an expanding window rather than the length you chose.

## Keep the future out of the history {#keep-the-future-out-of-history}

A backtest leaks when a window's model sees a reading from the hours it is asked to forecast. The reading can reach the model in several ways: through the history, through a feature, or through a scale computed from data that includes the target. Hewamalage, Ackermann and Bergmeir describe rolling-origin evaluation as prone to exactly this, because the test data of one window becomes training data of the next. In forecasting, they note, the leak is easier to make and harder to avoid than in other machine learning tasks (Hewamalage, Ackermann and Bergmeir, 2022, arXiv:2203.10716, section 3.4).

One rule closes the history path. Each window's history is the readings whose timestamps fall in the eight weeks before its cutoff, and nothing at or after the cutoff. In the book's code, `history_before` keeps the rows with `ds` from the cutoff minus 1,344 hours up to, but not including, the cutoff. The reading at the cutoff itself belongs to the target day, so the same comparison excludes it. Membership is decided by timestamps, not by row positions, so a missing row cannot shift a window by an hour. `history_before` also raises an error unless every client has exactly 1,344 rows in the window.

The cut is made from the cutoff, and the window's own first hour is the cutoff. A cut that is one hour too generous passes the first target reading into the history, and nothing in a forecast shows it. The example below makes that error visible.

Example `history-cut-check` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""One window's history, cut by its cutoff: its first and last timestamps, and what a cut at or before the cutoff adds."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.settings import HISTORY_HOURS, LEAD, show

df = load([LEAD])
cutoff = pd.Timestamp("2014-12-29")
hist = history_before(df, cutoff)
show("history rows", len(hist))
show("first history timestamp", hist["ds"].min().strftime("%Y-%m-%d %H:%M"))
show("last history timestamp", hist["ds"].max().strftime("%Y-%m-%d %H:%M"))

wrong = df[(df["ds"] >= cutoff - pd.Timedelta(hours=HISTORY_HOURS)) & (df["ds"] <= cutoff)]  # an off-by-one cut
show("history rows with ds at or before the cutoff", len(wrong))
show("target-day readings in that cut", int((wrong["ds"] == cutoff).sum()))
```

Output:

```text
history rows: 1344
first history timestamp: 2014-11-03 00:00
last history timestamp: 2014-12-28 23:00
history rows with ds at or before the cutoff: 1345
target-day readings in that cut: 1
```

The example takes the window of Dec 29, 2014 and prints the first and last timestamps of its history. It then counts a cut that keeps the reading at the cutoff, `ds <= cutoff`. The history runs from 2014-11-03 00:00 to 2014-12-28 23:00, and holds 1344 rows. The cut with `ds <= cutoff` holds 1345 rows, so the target day's first reading, which is the cutoff hour, has entered the history. A count one row too high is the sign of that error.

The same care applies to the scale. `evaluate` in `utilsforecast` takes a training frame for its scale, and it cuts that frame by time only when the forecast frame carries a `cutoff` column. Then it keeps the training rows with `ds` at or before the cutoff, which includes the cutoff hour itself (utilsforecast 0.2.17, `evaluation.py`). This chapter does not use that option. Its scale comes from `scoring.book_scale`, which passes only the rows before the first cutoff, and the frame it scores has no `cutoff` column.

**Working rule:** Slice each window's history by its cutoff, never by the start of its test window, and pass a library only the rows it may use. Check the first and last timestamps of every history, and make sure the last one is an hour before the cutoff.

## Meet the clock changes {#meet-the-clock-changes}

The data has two hours that break the simple picture of one reading per clock hour. On the March change day, the local clock goes from 00:59 to 02:00, so the 01:00 hour does not exist on the clock. Mainland Portugal is on Greenwich Mean Time in winter, and the EU moves the clocks at 01:00 Greenwich Mean Time, which is 02:00 local time (Directive 2000/84/EC, Article 2). On the October change day, the clock goes back from 02:00 to 01:00, so the 01:00 hour happens twice. The file has one row for 01:00 per day, flagged in the book's data as `clock_change_gap` or `clock_change_repeat`.

The book reads the file under one stated assumption, which every later chapter relies on. A reading's timestamp `ds` is the start of its hour in local clock time, and the index is one naive hourly index with no time zone. The March evidence supports this reading. The dataset's own note says the 01:00 values on the March change day are zero for all clients (Dataset 321, UCI Machine Learning Repository, https://doi.org/10.24432/C58C86). The file mostly agrees, as the first subsection shows, and the second shows the two hours of energy in the October label.

### The March hour that reads zero {#the-march-hour-that-reads-zero}

On Mar 30, 2014, the 01:00 label reads zero for 5 of the eight clients in the subset. The others read a small amount, not an hour of demand. The census covers all thirty clients:

Example `clock-change-census` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""The clock-change hours of all thirty clients: how many read zero, and how each compares with its neighbours."""
from lib.electricity import load
from lib.quirks import clock_ratios
from lib.settings import show

r = clock_ratios(load())
gap = r[r["quirk"] == "clock_change_gap"]
repeat = r[r["quirk"] == "clock_change_repeat"]
show("gap rows", len(gap))
show("gap rows that read zero", int((gap["y"] == 0).sum()))
show("gap rows that read above zero", int((gap["y"] > 0).sum()))
show("gap rows below 5 percent of their neighbours", int((gap["ratio"] < 0.05).sum()))
show("gap rows at or above 5 percent of their neighbours", int((gap["ratio"] >= 0.05).sum()))
show("median gap ratio to neighbours", gap["ratio"].median(), digits=3)
show("repeat rows", len(repeat))
show("median repeat ratio to neighbours", repeat["ratio"].median(), digits=3)
```

Output:

```text
gap rows: 57
gap rows that read zero: 40
gap rows that read above zero: 17
gap rows below 5 percent of their neighbours: 55
gap rows at or above 5 percent of their neighbours: 2
median gap ratio to neighbours: 0.000
repeat rows: 58
median repeat ratio to neighbours: 1.948
```

It finds 57 flagged client-hours on the two March change days. Of those, 40 read zero, 17 read above zero, and 55 sit below 5 percent of the neighbouring hours, which is what this chapter means by near zero. The median ratio to the neighbours is 0.000.

The data say zero or near zero, which is enough for the rule. The meter recorded nothing for an hour that did not occur on the clock, so the reading is not demand.

Seasonal naive copies the last day's values forward, so the forecast for 01:00 on Mar 30 is the demand of Mar 29 at 01:00. That is an ordinary hour, and where the reading is zero, the error is the whole forecast.

Predict before you run the next example: the cutoff of Mar 31 looks back over the 24 hours before it, which include the zero. How large is the error at 01:00 on Mar 31 compared with an ordinary hour? The example runs the seasonal naive forecast over the 15 daily cutoffs from Mar 23 to Apr 6, 2014, first without any rule and then with the rule from the next section:

Example `clock-gap-daily-cutoffs` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Seasonal naive around the March clock change, for the subset of eight clients: the raw failure, then the rule."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import filled_history, mae_of, mask_clock_changes, median_client_ratio, seasonal_naive_at
from lib.settings import SUBSET8, show

cutoffs = pd.date_range("2014-03-23", "2014-04-06", freq="D")  # 15 daily cutoffs around Mar 30, 2014
next_day = pd.Timestamp("2014-03-31 01:00")
df = load(SUBSET8)[["unique_id", "ds", "y", "quirk"]]
masked = mask_clock_changes(df)

raw = seasonal_naive_at(df, cutoffs, lambda c: history_before(df, c))
gap = raw["quirk"] == "clock_change_gap"
at_next_day = raw["ds"] == next_day
show("gap hours in actuals", int(gap.sum()))
show("gap hours that read zero", int((raw[gap]["y"] == 0).sum()))
show("gap-hour MAE with no rule", mae_of(raw[gap]))
show("other-hour MAE with no rule", mae_of(raw[~gap]))
show("median client ratio, gap hour to other hours, no rule", median_client_ratio(raw, gap, ~gap))
show("next-day MAE at 1am with no rule", mae_of(raw[at_next_day]))
show("next-day 1am forecasts that are zero, no rule", int((raw[at_next_day]["SeasonalNaive"] == 0).sum()))
show("median client ratio, next-day 1am to other hours, no rule", median_client_ratio(raw, at_next_day, ~gap))

no_fill = seasonal_naive_at(masked, cutoffs, lambda c: history_before(masked, c))
show("NaN forecasts without the fill", int(no_fill["SeasonalNaive"].isna().sum()))

fixed = seasonal_naive_at(masked, cutoffs, lambda c: filled_history(masked, c))
show("next-day MAE at 1am with the rule", mae_of(fixed[fixed["ds"] == next_day]))
show("other-hour MAE with the rule", mae_of(fixed[fixed["quirk"] != "clock_change_gap"]))
```

Output:

```text
gap hours in actuals: 8
gap hours that read zero: 5
gap-hour MAE with no rule: 2322.69
other-hour MAE with no rule: 234.21
median client ratio, gap hour to other hours, no rule: 7.93
next-day MAE at 1am with no rule: 2393.01
next-day 1am forecasts that are zero, no rule: 5
median client ratio, next-day 1am to other hours, no rule: 9.92
NaN forecasts without the fill: 8
next-day MAE at 1am with the rule: 274.41
other-hour MAE with the rule: 228.31
```

The example prints 8 gap hours in the actuals, one per client, and 5 of them read zero. The MAE at those hours is 2322.69 kWh, and at every other hour in the same windows it is 234.21 kWh. Both are pooled, so the largest client sets most of each number. Per client, the median ratio of the gap-hour error to that client's error at other hours is 7.93. The forecast for 01:00 on Mar 31 copies the zero for 5 clients, and its pooled error there is 2393.01 kWh. The median client's ratio on that day is 9.92. The method is wrong on the change hour, and wrong by about as much the day after, because it copied the zero.

**Working rule:** Treat a 01:00 reading of zero on a March clock-change day as a missing hour, not as zero demand. Keep it out of a model's history and out of the scores, and do not let a seasonal method copy it into the next day.

### The October hour that holds two {#the-october-hour-that-holds-two}

On Oct 26, 2014, the 01:00 label holds about two hours of energy. The census puts the median ratio of that hour to its neighbours at 1.948, over the 58 flagged client-hours in the file. The dataset's note agrees: the 01:00 values aggregate two hours of consumption (Dataset 321, UCI).

The failure is the reverse of the March one. On the change day, seasonal naive forecasts the 01:00 label from the day before, which is an ordinary hour, and the actual is about double that. The day after is worse. The cutoff of Oct 27 copies the doubled value, so the forecast for 01:00 on Oct 27 is about twice an ordinary hour, and the actual is ordinary.

The next example runs the same comparison over the 15 daily cutoffs from Oct 19 to Nov 2, 2014:

Example `clock-repeat-daily-cutoffs` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Seasonal naive around the October clock change, for the subset of eight clients: the raw failure, then the rule."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import filled_history, mae_of, mask_clock_changes, median_client_ratio, seasonal_naive_at
from lib.settings import SUBSET8, show

cutoffs = pd.date_range("2014-10-19", "2014-11-02", freq="D")  # 15 daily cutoffs around Oct 26, 2014
next_day = pd.Timestamp("2014-10-27 01:00")
df = load(SUBSET8)[["unique_id", "ds", "y", "quirk"]]
masked = mask_clock_changes(df)

raw = seasonal_naive_at(df, cutoffs, lambda c: history_before(df, c))
repeat = raw["quirk"] == "clock_change_repeat"
at_next_day = raw["ds"] == next_day
show("repeat hours in actuals", int(repeat.sum()))
show("repeat-hour MAE with no rule", mae_of(raw[repeat]))
show("other-hour MAE with no rule", mae_of(raw[~repeat]))
show("median client ratio, repeat hour to other hours, no rule", median_client_ratio(raw, repeat, ~repeat))
show("next-day MAE at 1am with no rule", mae_of(raw[at_next_day]))
show("median client ratio, next-day 1am to other hours, no rule", median_client_ratio(raw, at_next_day, ~repeat))

no_fill = seasonal_naive_at(masked, cutoffs, lambda c: history_before(masked, c))
show("NaN forecasts without the fill", int(no_fill["SeasonalNaive"].isna().sum()))

fixed = seasonal_naive_at(masked, cutoffs, lambda c: filled_history(masked, c))
show("next-day MAE at 1am with the rule", mae_of(fixed[fixed["ds"] == next_day]))
show("other-hour MAE with the rule", mae_of(fixed[fixed["quirk"] != "clock_change_repeat"]))
```

Output:

```text
repeat hours in actuals: 8
repeat-hour MAE with no rule: 637.18
other-hour MAE with no rule: 397.96
median client ratio, repeat hour to other hours, no rule: 6.98
next-day MAE at 1am with no rule: 1524.26
median client ratio, next-day 1am to other hours, no rule: 7.53
NaN forecasts without the fill: 8
next-day MAE at 1am with the rule: 184.22
other-hour MAE with the rule: 394.23
```

The example prints 8 repeat hours in the actuals. Its pooled MAE at those hours is 637.18 kWh, against 397.96 kWh at every other hour in the windows, and the pooled next-day error at 01:00 is 1524.26 kWh. Pooled, the gap looks smaller than it is, because the largest client's errors are large at every hour. Per client, the median ratio of the change-hour error to that client's error at other hours is 6.98, and on the next day it is 7.53. The doubled value is copied forward, so a reader who treats the raw October label as an ordinary hour will under-forecast one hour and over-forecast the next.

**Working rule:** Treat the October 01:00 label as two hours of energy in one slot, and never as an ordinary hour. Do not halve it to make it look like one, for the reason the next section gives.

## Mark clock-change hours as missing {#mark-clock-change-hours-as-missing}

The rule the book uses is a choice, and this section states it in one place so that every later chapter can call the same code. Both 01:00 hours, the March gap and the October repeat, are set to missing in the history and in the scores, so a masked hour is never scored. A model that takes missing values skips the hour. A model that cannot, such as seasonal naive, reads a filled value instead, because a missing value would copy into the next day's forecast. Either way the hour is never scored, and the forecast still produces a value for its label, because the output grid must stay complete. The fill is the mean of the hour before and the hour after, taken from the history before the cutoff only. It is a rule of thumb for an hour that sits between two ordinary ones, and it is labelled as one.

Halving the October label instead would give each real hour half of its reading, which assumes both hours used the same energy. The data card does not show that, so the book does not do it.

The daily examples show what the fill does. Without it, the forecast for 01:00 on Mar 31 is missing for 8 clients. With the mask and the fill, the next-day error at that hour is 274.41 kWh, against 2393.01 kWh with no rule. The other hours' error is 228.31 kWh, against 234.21 kWh. The October example gives the same picture: 8 missing forecasts without the fill, and a next-day error of 184.22 kWh with the rule, against 1524.26 kWh without it.

The year of Sunday cutoffs is a different test. It applies the mask to the scores, and its fill has nothing to do:

Example `clock-masked-backtest` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
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
```

Output:

```text
masked hours in scored windows: 16
scored hours without the mask: 9936
MAE without the mask: 382.02
mean MASE without the mask: 0.97
scored hours with the mask: 9920
MAE with the mask: 380.25
mean MASE with the mask: 0.96
```

It prints 16 masked hours in the scored windows, the March and October hours of the subset. Scored without the mask, the year's pooled MAE is 382.02 kWh and its mean MASE is 0.97. With the mask, the pooled MAE is 380.25 kWh and the mean MASE is 0.96, over 9920 hours rather than 9936. The difference comes from the removed hours. The Sunday sample cannot show the fill at all, because seasonal naive reads only the day before each cutoff, which is a Saturday for every Sunday cutoff, and no Saturday holds a clock change.

**Working rule:** Mark both clock-change hours missing in every history and every score, count the masked hours in your report, and fill them from the history before the cutoff only when the model cannot take missing values. If the count of masked hours changes from one run to the next, the sample or the file's flags have changed, and you should find out why before you rerun the scores.

## Check a backtest for leakage {#check-a-backtest-for-leakage}

Every window in a backtest should be built from data available at its cutoff, so the check for a leak is simple to state. A feature for a window must have the same value whether it is computed from the history cut at the cutoff or from the whole series. If the two values differ, the feature read a reading after the cutoff, and the backtest flatters the method. This is the shift test. It is cheap to run, and it catches a mistake that the backtest cannot catch on its own, because a leaking feature scores well by design.

The test has two halves, and each catches what the other misses. The example takes the lead client, `MT_014`, and defines three features over its hourly readings. The first is a trailing mean: the average of the 24 hours up to and including each hour, which reads nothing after its hour. The second is the same mean shifted one hour forward, so each value is the average of a window that ends one hour later, and it reads the first hour after the cutoff. The third is a lag of one hour, the most common day-ahead leak. The history half compares each feature on the rows of the eight weeks before each of the three evaluation cutoffs, Dec 29, 30 and 31, 2014. The target half compares the 24 hours that each cutoff forecasts, computed from the readings before the cutoff only. Both versions start from the same first reading, so the warm-up of a rolling mean matches on both sides. Computed from different starts, the warm-up and floating-point rounding would show as false differences, which is why the example compares with a tolerance:

Example `leakage-shift-check` (Python 3.13.16 · numpy 2.4.6 · pandas 2.3.3), passing in Edition 2026.11.1:

```python
"""Shift test: a feature must read nothing from its cutoff on, on the history rows and on the target hours."""
from lib.electricity import load
from lib.leakage import history_test, lag, peeking_mean, target_test, trailing_mean
from lib.settings import EVAL_CUTOFFS, LEAD, show

y = load([LEAD]).set_index("ds")["y"]

compared, honest = history_test(y, trailing_mean)
_, peeking = history_test(y, peeking_mean)
_, lag1_history = history_test(y, lag(1))
show("cutoffs", len(EVAL_CUTOFFS))
show("rows compared", compared)
show("rows differing for the trailing mean", honest)
show("rows differing for the peeking mean", peeking)
show("rows differing for lag 1", lag1_history)

targets, lag1_target = target_test(y, lag(1))
_, lag24_target = target_test(y, lag(24))
show("target hours compared", targets)
show("target hours differing for lag 1", lag1_target)
show("target hours differing for lag 24", lag24_target)
```

Output:

```text
cutoffs: 3
rows compared: 4032
rows differing for the trailing mean: 0
rows differing for the peeking mean: 3
rows differing for lag 1: 0
target hours compared: 72
target hours differing for lag 1: 69
target hours differing for lag 24: 0
```

The example prints 4032 history rows across the three cutoffs. The trailing mean differs on 0 of them. The shifted mean differs on 3 rows, one for each cutoff: the last hour before each cutoff, whose value now depends on the reading at the cutoff itself. The lag of one hour differs on 0 history rows, because every row it reads lies in the past. That is why the history half alone passes it. On the target hours, the lag of one hour differs on 69 of the 72 hours. For every target hour after the first, the reading it uses is in the day being forecast. The lag of 24 hours differs on 0 hours, because it reads the same hour of the day before, which was known at each cutoff.

The shift test checks features and nothing else. It does not check the scale, the fill or the model's own code, which is why the earlier sections set those rules separately. Run it on every feature a model reads, at several cutoffs spread through the year, and include a cutoff on a clock-change day if the feature reads the hour before it.

When a feature fails the test, do not fix the score. Move the feature back until it reads only what was known at its cutoff, then run the test again until the count is zero.

**Working rule:** Keep every lag at least the horizon, 24 hours, so that the reading a lag uses for any target hour was known at the cutoff. Before you trust a backtest with features, run both halves of the shift test on every feature, at several cutoffs spread through the year, and require zero differing rows for every feature the model reads. A feature that differs is reading the future, so fix or remove it before you score anything.

## What goes wrong in production {#what-goes-wrong-ch3}

A backtest is a sample of the past, and the sample is chosen. Every clock change falls on the last Sunday of March or October (Directive 2000/84/EC, Articles 2 and 3), so a Sunday sample reaches every change. A sample of Mondays would reach the day after each change without reaching the change hour itself, so the choice of days changes what the backtest can see. Record which dates the sample covers, and rerun the clock check when the sample's dates change.

Calendar effects are a separate sample problem. One of the 52 Sunday cutoffs is a Portuguese holiday: Easter Sunday, Apr 20, 2014, which the `holidays` package lists for Portugal. The example counts it, 1 of 52 windows. The held-out week contains Dec 25, 2014, a national holiday in Portugal, and a week of ordinary days and one holiday gives a different score from a week of ordinary days alone. A backtest that uses holiday features must count the holidays in its windows, and say how many fall in the sample.

A pooled error hides the windows that went wrong. A year of windows can average to a respectable number while one month, or one client, carries the error. Break the scores down by month and by client before you report one figure, and look at the worst windows, not only the average.

The masked count follows the calendar flag, not the readings. It changes when the sample's dates or the file's flags change, and it cannot see drift in the readings. Count the masked hours on every run, and alarm on a change in the count, because it is the cheapest signal that the sample or the file has changed. Drift in the readings needs the census: the gap hours that read zero, and the repeat hours against their neighbours. Chapter 10 returns to this in the running log.

Finally, a backtest that passes the shift test can still leak through the scale or the fill, if either is taken from data after the cutoff. The checks in this chapter cover those paths in the examples and the rules, not in every library a reader might use. A reader who adds a library should read how it cuts its training data, as the [default of `cross_validation`](#roll-the-cutoff-forward) shows.

**Working rule:** Run the clock and shift checks again on every data refresh, and before any change to the sample's dates, the history length or the scale. Keep the masked-hour count, the census counts and the shift-test counts in the run log next to the scores, so that a later change in either can be traced to its cause.

## Decisions this chapter made {#decisions-ch3}

- The backtest uses the Sunday cutoffs of 2014. Every clock change falls on a Sunday, so the sample reaches each change, and both of 2014's changes are in it.
- The history of every window is the 1,344 hours before its cutoff, cut by the cutoff, and the length is set in the code, not left to a library default.
- The timestamp `ds` is the start of its hour in local clock time, with no time zone, and the book reads the file under that assumption.
- Both clock-change hours are masked in every history and every score. A model that cannot take missing values reads the mean of the neighbouring hours from history before the cutoff.
- Halving the October hour is rejected, because it assumes the two real hours used the same energy, which the data does not show.
- The headline is the mean per-client MASE, on the one scale of Chapter 2 through `scoring.book_scale`. Pooled MAE is the second line, with the largest client's share printed.
- A client with no reading before the first cutoff is left out of MASE. A late starter's hours before its first reading are left out of every score. Chapter 4 owns the start rule for histories.
- The shift test runs on every feature, both halves. Every lag is at least the horizon, and a feature that differs at any cutoff is not used.
- The examples print labelled lines, and the prose binds to them. When a library update changes a number, the build changes the chapter's figure, and nobody retypes it.
