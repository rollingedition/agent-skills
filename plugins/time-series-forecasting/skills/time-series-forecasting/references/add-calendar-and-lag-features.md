---
title: "Time Series Forecasting"
chapter: "Add calendar and lag features"
chapter_id: add-calendar-and-lag-features
book: time-series-forecasting
edition: 2026.11.2
verified: 2026-11-11
edition_code: RHYP-H8RM
canonical: https://rollingedition.com/time-series-forecasting/add-calendar-and-lag-features
license: CC BY 4.0
attribution: "“Add calendar and lag features,” chapter 5 of Time Series Forecasting, Edition 2026.11.2, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/add-calendar-and-lag-features. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Add calendar and lag features

By the end of this chapter you can turn one client's hourly history into a feature table, add lags and calendar and holiday features that a day-ahead forecast is allowed to see, measure what each feature adds on the same windows, and catch a lag that reads the day being forecast.

The statistical models in Chapter 4 see only a series. They know its level and its daily rhythm, and nothing else. They do not know that Dec 25, 2014 was a public holiday, that a Monday differs from a Sunday, or that demand moves with the season. In Chapter 1, the seasonal naive baseline had its worst day on Dec 26, the day after Christmas, because it copied the holiday's readings forward. A gradient-boosting model can take such facts in as columns. This chapter adds the calendar and holiday columns for the supplier's eight-client subset and checks each one before it counts. The holiday flag does not repair the Dec 26 failure, because Dec 26 is not a holiday. The feature that would repair it, a day-after-holiday flag, is also known in advance, but this chapter does not build it, and its standard windows do not score a holiday at all.

## Turn history into features {#turn-history-into-features}

The table comes first, because every feature in this chapter is a column of it. A feature table has one row for each hour a model must predict. Each row holds the value to predict, which the book calls the target, and the features: the readings and facts the model may use for that hour. A gradient-boosting model learns a mapping from the columns to the target, one row at a time, so the table is the whole of what the model can know.

The features of a row must be known at the cutoff of the window that forecasts it, because the forecast is made there. The target is the reading at the hour. The model needs two kinds of row. Training rows are the hours of the history before the cutoff, each with its own features and its own reading as the target. Forecast rows are the 24 hours after the cutoff, with features but no target. The model is fitted on the first kind and predicts the second.

Take the cutoff at 00:00 on Dec 30, 2014. Its forecast rows are the 24 hours of Dec 30, from 00:00 to 23:00, and each has a blank target. Its training rows run back eight weeks, to Nov 4, 2014, one row per client and hour, with the reading as the target. Take the row for Dec 15 at 18:00: its target is the reading at that hour, and its features are readings from earlier hours, such as the reading 24 hours before. No row is a daily total.

For the supplier, one window's training table is built from the 1,344 hours of history before its cutoff, eight weeks, for each client in `SUBSET8`. The eight clients are stacked in one table, and the same construction repeats for every decision window and for the three standard cutoffs, Dec 29, Dec 30 and Dec 31, 2014. The first week of history has no reading a week earlier, so it leaves the table: 1,344 hours less 168 hours leaves 1,176 rows per client in each window. One model is fitted per window on that window's history alone, so no training row comes from the days being forecast.

For the supplier's model the columns are the two lags, the hour of the day, and the target `y`. The calendar and holiday columns come later in the chapter. The library builds this table for you. `MLForecast` in `mlforecast` 1.1.0 takes the series and produces the training rows in `fit` and the forecast rows in `predict`. Two of its defaults matter here. A training row whose features are missing is dropped (`dropna=True`, in `mlforecast/core.py`), and the first hours of each history drop out because they have no reading a week earlier. Nothing in the library stops a feature from reading the hour it predicts. The rule that stops it is the one you write and check.

**Working rule:** Build every feature row as if the cutoff were the last reading you have. A feature for a forecast hour must be computable from readings at or before the cutoff of its window. Before any shift test, ask whether the feature is known at the cutoff. Then check it with the [shift test from Chapter 3](#check-a-backtest-for-leakage), and do not train on a table you have not checked.

## Add lags the forecast can see {#add-lags-the-forecast-can-see}

The first features to put in that table are lags, earlier readings of the same client. The lag of k hours for the hour t is the reading at t minus k. Lags are the cheapest way to give a model the rhythm of a series: a lag of 24 is the reading at the same hour yesterday, and a lag of 168 is the reading at the same hour a week ago. The model learns how much to trust each one. The lag of 168 also reads a whole week back, which is the same weekday, so it carries the weekly pattern without a weekday column.

Whether a lag is known depends on the horizon. A forecast made at 00:00 covers the 24 hours from the cutoff. Call the hours of that day 0 to 23, counted from the cutoff. A lag of k reads hour j minus k, so for the target hour j it reads a reading before the cutoff only when j minus k is negative. That must hold for every j from 0 to 23, which means k must be 24 or more. A lag of 1 is known for the first hour, because it reads the last reading before the cutoff. For the other 23 hours it reads a reading the forecast does not have.

The table below shows the three kinds of target hour in that day-ahead forecast, for a cutoff at 00:00. Hour 0 is the first hour after the cutoff, and hour 23 is the last.

| Target hour | Lag 1 reads | Lag 1 known at cutoff | Lag 24 reads | Lag 24 known at cutoff |
| --- | --- | --- | --- | --- |
| 00:00 (hour 0) | 23:00 the day before | yes | 00:00 the day before | yes |
| 01:00 (hour 1) | 00:00 of the forecast day | no | 01:00 the day before | yes |
| 23:00 (hour 23) | 22:00 of the forecast day | no | 23:00 the day before | yes |

The supplier's model uses two lags, 24 and 168. Both are known for every hour of the day-ahead forecast, so the model never needs a reading that does not yet exist. The example that builds the feature sets, [lgbm-feature-sets](https://github.com/rollingedition/book-time-series-forecasting/blob/953a258e81dbd2d9435cf15185da38a7d3a7a49c/examples/lgbm-feature-sets.py), passes these two lags to `MLForecast`, and the rest is the library's job.

The [clock rule from Chapter 3](#mark-clock-change-hours-as-missing) reaches the lags too. The Mar 30, 2014 gap hour is set to missing, so any feature that reads it is missing as well. The example takes the history of an Apr 1, 2014 cutoff. It holds 1 masked hour, and 1 row has a lag that reads it: the row 24 hours after the gap. Before each window's model is fitted, its masked hours are filled from that window's own history: each takes the mean of the hour before and the hour after, and reads nothing after the cutoff. The masked hour is then a filled reading, so the row that reads it keeps a value, and LightGBM never receives a missing value from a lag. The rule is a stated choice, not a measured optimum. The count printed beside it is what a reader should check.

**Working rule:** Use only lags at least as long as the horizon. With a 24-hour horizon that means 24 hours or more, and this book uses 24 and 168. A shorter lag needs a reason, and a model that uses one must pass the shift test before anyone trusts its score. Keep the clock rule on the lags, and count the rows whose lags read a masked hour, and the hours filled from history.

## Add calendar and holiday features {#add-calendar-and-holidays}

Lags use readings. Calendar features are the other kind: facts about the target hour itself, its hour of day, its day of the week and its month. They are known in advance, because the clock states them before any reading exists. They need no lag and no cutoff rule. Their value at a target hour cannot depend on any reading, so the shift test has nothing to catch.

The supplier's demand follows the day. The hour of day repeats what the lags already carry: the daily rhythm. The weekday adds what they do not. It tells the model that Saturday and Sunday differ from the working days. The month is the third column, and it is a weak one with this history. Eight weeks split into the first four weeks and the last four, so `month` can separate only two halves of one month, and every forecast hour falls in December. The book uses three mlforecast date features, named by their attribute: `hour`, `dayofweek` and `month`. The weekday column already holds the weekend, so the book adds no separate weekend flag. In pandas, `dayofweek` counts Monday as 0 and Sunday as 6, so Saturday and Sunday are the two values a tree must separate from the rest. A tree can split on that in one step, which is why the weekday is cheap to test.

A public holiday does not follow the weekday. A model with only weekday features reads Dec 25, 2014 as an ordinary Thursday, and it reads a holiday on a Sunday as an ordinary Sunday. The holiday feature addresses this. It is a function of the timestamp, `is_holiday` in the shared module `examples/lib/features.py`, which returns 1 on a Portuguese national holiday and 0 otherwise. mlforecast accepts such a function as a date feature and names its column after the function. The holidays come from the `holidays` package 0.108, under the MIT licence, through `holidays.country_holidays("PT", years=[2013, 2014])`. For the two years in the data, the package lists 18 dates. The list is not shipped with the book. It is built when the example runs, from the package's own calendar.

The standard evaluation cutoffs are Dec 29, 30 and 31, and none of their 72 hours per client is a holiday. The held-out week's Dec 25 is outside them, so the feature's effect on that day is not scored in this chapter. On the standard cutoffs, it reaches the scores only through the training history, which contains the holidays of Dec 8 and Dec 25, 2014.

The holiday list is a fact known in advance, like the weekday. It comes from a published calendar and not from the readings, so it cannot leak a reading from the target day. Before any shift test, ask whether the feature's value at each target hour is knowable at the cutoff. Calendar features pass that by construction, and a lag passes only when it is at least as long as the horizon.

**Working rule:** Add the calendar features the case's rhythm needs, and keep each one only if it helps on the same windows, as the next section measures. For holidays, use a calendar that covers every year in your data and every year you will forecast, and print how many holidays it holds for those years. A count of zero for a forecast year means the list is missing that year, not that the year had no holidays.

## Choose on decision windows {#choose-on-decision-windows}

The feature set is chosen on decision windows, and never on the standard cutoffs, which are the windows the book reports. There are two kinds. The first is four ordinary cutoffs, Nov 25, Nov 26, Dec 2 and Dec 3, 2014. The second is seven holiday cutoffs: the Portuguese national holidays of 2014 before Dec 25 whose eight-week history is complete, Apr 18, Apr 20, Apr 25, May 1, Jun 10, Aug 15 and Dec 8. The ordinary windows hold no holiday, so a holiday feature could never win on them. The holiday windows are where it can. The choice therefore uses all eleven windows, because one of its sets holds a holiday feature. The standard cutoffs are scored after the choice, and the example prints them beside it. They choose nothing.

The holiday flag acts in two ways. On the decision windows it is on for scored hours, so it can change a forecast. On the standard cutoffs no holiday falls in a scored hour, so the flag changes those scores only through training.

**Working rule:** Choose a feature on windows that come before the held-out week and hold the kind of day the feature is for: a holiday feature needs holiday windows. The standard cutoffs are reported beside the choice and never used to make it.

## Measure what each feature adds {#measure-what-each-feature-adds}

A feature is worth keeping when it lowers the error on windows the model did not train on. To measure one, hold everything else fixed: the same windows, the same history, the same settings. The example fits three feature sets, one at a time. The first has lags only. The second adds the calendar features. The third adds the holiday feature to them. Each set is fitted once per window, with one model for all eight clients of `SUBSET8`, and each is compared with seasonal naive on the same windows.

The example reports two scores. The first is the MAE pooled over every client-hour in the windows, the single number for the whole supplier. The second is MASE for each client, averaged over the eight clients. MASE divides each client's error by a scale: the mean absolute error that seasonal naive makes in sample on that client's own readings. The book uses one scale function everywhere, `scoring.book_scale`. The scale reads every reading before the first scored window of the set, Apr 18, 2014 at 00:00, with clock-change hours masked, so it does not depend on the windows scored and cannot leak. One client needs care. MT_115 starts reading on Jan 14, 2014, and the zeros before its first reading are left out of its scale, because it is counted from its first reading. [Chapter 4](#meet-the-late-starters) teaches that rule for late starters.

Example `lgbm-feature-sets` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.2:

```python
"""Choose the feature set of a global LightGBM forecast of SUBSET8 on the decision windows (B-5, B-9, B-10): four ordinary
cutoffs and seven 2014 holidays before Dec 25. Each set is fitted scaled and unscaled. The standard cutoffs are reported
after the choice, and they choose nothing."""
import pandas as pd

from lib.backtest import history_before
from lib.electricity import load
from lib.features import CALENDAR, PT_HOLIDAYS, is_holiday, rows_reading_missing, score_feature_sets
from lib.panel import DECISION_CUTOFFS, HOLIDAY_DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, LEAD, SUBSET8, show

LAGS = [24, 168]
FEATURE_SETS = {"lags_only": [], "with_calendar": CALENDAR, "with_holidays": CALENDAR + [is_holiday]}
MODELS = ["SeasonalNaive", *FEATURE_SETS, *[f"unscaled_{name}" for name in FEATURE_SETS]]
DECISION = sorted([*DECISION_CUTOFFS, *HOLIDAY_DECISION_CUTOFFS])
raw = load(SUBSET8)

forecasts, scored, per_client = score_feature_sets(raw, DECISION, LAGS, FEATURE_SETS, DECISION[0])
show("clients", forecasts["unique_id"].nunique())
show("decision windows", len(DECISION))
show("scored hours", len(scored))
show("Portuguese holidays in 2013 and 2014", len(PT_HOLIDAYS))
show("holiday hours in the decision windows", int(is_holiday(scored["ds"]).sum()))
for model in MODELS:
    show(f"MAE {model.replace('unscaled_', 'unscaled ')}", (scored["y"] - scored[model]).abs().mean())
for model in MODELS:
    show(f"mean MASE {model.replace('unscaled_', 'unscaled ')}", per_client[model].mean(), digits=3)
for model in MODELS:
    show(f"MASE MT_268 {model.replace('unscaled_', 'unscaled ')}", per_client.loc["MT_268", model], digits=3)

# The standard cutoffs, reported beside the choice above. Nothing is chosen from them.
_, _, standard = score_feature_sets(raw, EVAL_CUTOFFS, LAGS, FEATURE_SETS, EVAL_CUTOFFS[0])
for model in MODELS:
    show(f"standard cutoffs, mean MASE {model.replace('unscaled_', 'unscaled ')}", standard[model].mean(), digits=3)

# Clock-change check: the history of a 1 April 2014 cutoff holds the 30 March gap, which the feature rules must reach.
march = history_before(mask_clock_changes(load([LEAD])), pd.Timestamp("2014-04-01"))
show("masked hours in the history", int(march["y"].isna().sum()))
show("rows whose lag reads a masked hour", rows_reading_missing(march.set_index("ds")["y"], LAGS))
```

Output:

```text
clients: 8
decision windows: 11
scored hours: 2112
Portuguese holidays in 2013 and 2014: 18
holiday hours in the decision windows: 1344
MAE SeasonalNaive: 305.21
MAE lags_only: 280.57
MAE with_calendar: 270.57
MAE with_holidays: 267.40
MAE unscaled lags_only: 304.03
MAE unscaled with_calendar: 271.63
MAE unscaled with_holidays: 280.75
mean MASE SeasonalNaive: 0.934
mean MASE lags_only: 0.886
mean MASE with_calendar: 0.894
mean MASE with_holidays: 0.893
mean MASE unscaled lags_only: 1.115
mean MASE unscaled with_calendar: 1.119
mean MASE unscaled with_holidays: 1.139
MASE MT_268 SeasonalNaive: 0.840
MASE MT_268 lags_only: 0.797
MASE MT_268 with_calendar: 0.758
MASE MT_268 with_holidays: 0.789
MASE MT_268 unscaled lags_only: 0.855
MASE MT_268 unscaled with_calendar: 0.871
MASE MT_268 unscaled with_holidays: 0.936
standard cutoffs, mean MASE SeasonalNaive: 1.162
standard cutoffs, mean MASE lags_only: 1.057
standard cutoffs, mean MASE with_calendar: 1.165
standard cutoffs, mean MASE with_holidays: 1.134
standard cutoffs, mean MASE unscaled lags_only: 1.357
standard cutoffs, mean MASE unscaled with_calendar: 1.494
standard cutoffs, mean MASE unscaled with_holidays: 1.486
masked hours in the history: 1
rows whose lag reads a masked hour: 1
```

The example prints 2112 scored hours: eight clients, 11 windows of 24 hours each. Pooled, seasonal naive has an MAE of 305.21 kWh. The rest of this section explains the scaling.

The clients differ a great deal in size, so the largest clients' readings are many times the smallest's. A global model fits one loss over every client's rows, and here that loss is squared error in kWh, so the largest clients' errors set the splits and the small clients carry little weight. The example first runs each set without any scaling, and the failure shows in one line. The unscaled lags-only model has a mean per-client MASE of 1.115, worse than seasonal naive's 0.934. We think the cause is the loss, not the range of any one client. The scaled runs below remove the difference, which supports that reading. It is a judgement from these numbers, not a proof.

The scaled runs standardise each client's target with mlforecast's `LocalStandardScaler` (`mlforecast/target_transforms.py`), which subtracts the client's mean and divides by its standard deviation. Both come from the window's history before the cutoff, fitted inside `fit`, and `predict` only inverts them. No reading after the cutoff sets them, so the scaling passes the same test as the features. `make_forecaster` takes `scaled=True` by default, and Chapter 6 reuses that default.

Scaled, the comparison changes. The lags-only set has a mean per-client MASE of 0.886, against 0.934 for seasonal naive, so on this view it beats the baseline. Its pooled MAE is 280.57 kWh. The calendar set has a mean MASE of 0.894. That beats the baseline, but not lags alone, and its pooled MAE is 270.57 kWh. The holiday flag, added to the calendar set, brings the mean to 0.893 and the pooled MAE to 267.40 kWh. Chapter 4 set AutoETS and ARIMA as the bar a gradient-boosting model must beat. On the standard cutoffs, where ARIMA is scored on the same clients, cutoffs and scale, lags alone score 1.057 against ARIMA's 1.09.

By the working rule, only the lags stay. The per-client view decides it, and it is the view that matters to a client's forecast. The calendar set's mean MASE is above lags alone's. The pooled view points the other way here: the calendar set's pooled MAE is below lags alone's, and the holiday set's is lower still. The chapter reports both, as the rule asks, and does not tune the model to make them agree. The rule keeps a feature only when it lowers the error of the set it extends. The calendar set does not beat lags alone, so it is not kept. The holiday flag lowers the calendar set's mean by a hair, too little to count as a gain, and the set that holds it is still above lags alone. The flag is on for 1344 client-hours, 168 for each of the eight clients, so it had its chance on the holiday windows, and it does not earn a place. The book therefore hands Chapter 6 the lags-only set. The result is for eleven windows, which is a small test, and the chapter says so.

**Working rule:** Keep a feature set only when it lowers the mean per-client MASE against the set it extends, on the same windows. Report the pooled MAE beside it. Do not tune the model to make a disagreement between the two views go away.

## Catch a lag that leaks the future {#catch-a-lag-that-leaks}

The measurements above assume that each feature is known at its cutoff. A leak breaks that assumption. It is a feature that uses a reading the forecast cannot have at its cutoff. In the book's view, a leak is a likely reason a backtest looks better than the model will be, and it can be built by accident. One pattern builds the feature table once from the whole series, so each target hour carries its lag, and then scores the table's forecast rows as if they were out of sample. Nothing fails. The score is too good, and nothing in it says so.

The library adds a second trap of its own. `MLForecast` predicts recursively by default. For a 24-hour horizon it forecasts one hour, writes that forecast back as the reading for the next hour, and repeats (`_predict_recursive` in `mlforecast/core.py`). A lag of 1 therefore reads a forecast for every hour after the first, while training read actual readings for that lag. Calling that mismatch a leak is the book's judgement. It is one more reason to choose lags of 24 or more. With lags of 24 and 168, every step of the 24 reads actual readings, so the recursion never feeds this model its own forecasts. With `max_horizon` set, the library trains one model per horizon instead, and predicts with them in `_predict_multi`. The rule does not change with it: a feature must still be known at the cutoff of the window it forecasts.

The [shift test from Chapter 3](#check-a-backtest-for-leakage) carries over with one change: compare the lag at the target hours after the cutoff, not at the history rows. Compute the lag for each target hour twice: once from the history cut at the cutoff, and once from the whole series. Count the hours where the two differ. A lag of 24 agrees on every target hour, because each of the 24 hours reads a reading before the cutoff. A lag of 1 agrees only on the first hour.

Before you run the example, predict which model has the lower error: the one with a lag of 1, or the one without it. The example fits both, on the same training rows and the same settings, for each of the three standard cutoffs. The honest model uses lags 24 and 168. The leaky model adds a lag of 1, read from the whole series for the target hours, which is what the table built once would do.

Example `lag-leak-check` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.2:

```python
"""Catch a lag that leaks: a lag of 1 reads the hour before each target hour, which is not known at a 24-hour cutoff."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.features import fit_window_mae, lag_values
from lib.settings import EVAL_CUTOFFS, HORIZON, LEAD, show

y = load([LEAD]).set_index("ds")["y"].asfreq("h")
HONEST, LEAKY = [24, 168], [1, 24, 168]
CUTOFFS = pd.to_datetime(EVAL_CUTOFFS)


def shift_test(lag):
    """Target hours where the lag differs between the history cut at each cutoff and the whole series, and how many."""
    compared = differing = 0
    for c in CUTOFFS:
        targets = pd.date_range(c, periods=HORIZON, freq="h")
        honest = lag_values(y[y.index < c], lag, targets)
        whole = lag_values(y, lag, targets)
        same = (honest == whole) | (np.isnan(honest) & np.isnan(whole))
        compared += len(targets)
        differing += int((~same).sum())
    return compared, differing


show("cutoffs", len(CUTOFFS))
show("rows compared", shift_test(1)[0])
for lag in (1, 24, 168):
    show(f"rows differing for lag {lag}", shift_test(lag)[1])
show("MAE honest, lags 24 and 168", fit_window_mae(y, HONEST, CUTOFFS, leaky=False))
show("MAE leaky, lags 1, 24 and 168", fit_window_mae(y, LEAKY, CUTOFFS, leaky=True))
```

Output:

```text
cutoffs: 3
rows compared: 72
rows differing for lag 1: 69
rows differing for lag 24: 0
rows differing for lag 168: 0
MAE honest, lags 24 and 168: 5.36
MAE leaky, lags 1, 24 and 168: 2.87
```

The shift test compares 72 target hours, 24 for each window. The lag of 1 agrees on the first hour of each window, because that hour reads the last reading before the cutoff, which the forecast does have. It disagrees on the other 23. The test finds 69 rows that differ for a lag of 1, which is 23 for each window, and 0 rows for a lag of 24 and 0 for a lag of 168. The leaky model's MAE is 2.87 kWh, against 5.36 kWh for the honest model. The leaky model looks almost twice as good. The gap is the leak: its lag of 1 reads the hour before the target, which for most target hours is an hour of the forecast window itself. The honest model never sees that hour, so its error is the one that production will show.

**Working rule:** Run the shift test on every lag and every window feature before a model trains on it, and treat any differing row as a leak until you have shown otherwise. When an error falls sharply after you add a feature, check that feature first, before you credit it.

## What goes wrong in production {#what-goes-wrong-ch5}

The first failure is a holiday list that stops at the end of the data. The flag then reads zero for every day of the forecast year, and the model forecasts holidays as ordinary days. Nothing errors, and the first holiday shows up as a large miss on the dashboard. The count printed by the example is the check: a list for a new year that prints zero holidays is missing that year. A later version of `holidays` can also change its calendar, so pin the version, as the book does, and rerun the count after any upgrade.

The second is a lag shorter than the horizon, carried over from an hourly model that is used for a day-ahead forecast. The backtest scores it well, because the backtest was built from the whole series. In production, the later hours read the model's own forecasts. Compare the live error by hour of the day-ahead forecast with the backtest's own error by hour. A model without the leak should show about the error the backtest showed at each hour. Error that grows with the hour of the horizon, beyond that, is the sign of feedback from the model's own forecasts.

The third is the clock rule applied silently. Masked hours make some forecast features missing, and a pipeline can drop those rows, or fill those hours, without saying so. Print the masked hours and the rows they affect every time the history changes.

The fourth is a pooled score that hides the typical client. In the example, the unscaled lags-only model's pooled MAE is 304.03 kWh, below seasonal naive's 305.21 kWh. Its mean per-client MASE is 1.115, against 0.934. The supplier buys power for each client, so the per-client figure is the one that decides a client's forecast. A supplier that reports only the pooled MAE will sell the wrong forecast to the clients it hides. Report the per-client MASE next to the pooled figure, and look at the worst client first.

The last is a result that depends on the machine. LightGBM's [parameter reference](https://lightgbm.readthedocs.io/en/v4.7.0/Parameters.html) says `deterministic` gives stable results for the same data and the same parameters on the CPU device type, and warns that results can differ with other LightGBM versions, with binaries compiled by other compilers, or on other systems. The book sets `deterministic`, row-wise histograms, one thread and a fixed seed, under LightGBM 4.7.0. Those settings make the output repeatable on one machine with one thread count: the example gave identical output in three runs on the machine that recorded it. They do not promise agreement across machines, and the book has not tested that. The scores are quoted rounded, so the text reads well, and rounding does not make two machines agree. If a release machine prints different values, the recorded output needs a fresh recording, and the prose needs the same check.

**Working rule:** Run the example's checks on every refresh of the data and every upgrade of a library: the holiday count for each forecast year, the masked hours and the rows they reach, the shift test on every lag, and the per-client MASE beside the pooled MAE. A check that changes is a reason to stop and read the cause before the next forecast is published.

## Decisions this chapter made {#decisions-ch5}

The choices below are the ones a reader would have to make differently to change the results. Each one is a choice of the book, not a finding, and each is open to revision when a later edition measures something else.

- The handed-on model uses lags 24 and 168 only. Lag 1 appears only in the leak check, never in a forecast.
- The calendar set is `hour`, `dayofweek` and `month`. It is measured and not kept: on the per-client view it is worse than lags alone. There is no separate weekend flag, because the weekday carries the weekend.
- The holiday flag is measured only on top of the calendar set, on all eleven decision windows. It is not kept, because the set that holds it is still worse than lags alone. Chapter 6 gets the lags-only set.
- Holidays come from the `holidays` package for Portugal, for the two years in the data. The `is_holiday` function lives in `examples/lib/features.py`.
- Each client's target is scaled by default, with `make_forecaster(scaled=True)`. The scaler is fitted on each window's history only. The unscaled run is printed once, to show the failure that scaling corrects.
- Each window's masked clock-change hours are filled from that window's history before the fit, so no row is dropped for them and LightGBM never receives a missing value.
- The LightGBM settings are `LGBM_PARAMS` in `examples/lib/features.py`: deterministic, row-wise histograms, one thread and seed 0. They sit there, not in `settings.py`, which this chapter leaves unchanged.
- The MASE scale is `scoring.book_scale`. It starts at each client's first reading and reads the readings before the first decision window, Apr 18, 2014.
- On the decision windows, the lags-only model beats seasonal naive on mean per-client MASE. Eleven windows are a small test, and the chapter does not tune the model to change the result.
- The feature sets are chosen on the decision windows, not on the standard cutoffs or the held-out week. The holiday windows end on Dec 8, so the holiday's effect on Dec 25 is not measured in this chapter. Whether calendar features pay on a longer history is also not measured here.
- The leak check uses `MT_014`, one client, because the leak is a property of the lag and not of the client mix. The leak check fits one client, so its target is not scaled. The feature-set comparison uses `SUBSET8`.
- Chapter 6 reuses `make_forecaster`, `mlforecast_windows`, `fit_window_mae`, `lag_table` and `is_holiday` from `examples/lib/features.py`. `make_forecaster` scales by default.
