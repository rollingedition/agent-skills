---
title: "Time Series Forecasting"
chapter: "Forecast many clients with one model"
chapter_id: forecast-many-clients-at-once
book: time-series-forecasting
edition: 2026.11.9
verified: 2026-11-19
edition_code: GS5D-H19G
canonical: https://rollingedition.com/time-series-forecasting/forecast-many-clients-at-once
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Forecast many clients with one model,” chapter 6 of Time Series Forecasting, Edition 2026.11.9, examples passed Nov 19, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/forecast-many-clients-at-once. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Forecast many clients with one model

You finish this chapter with one global model for all thirty clients, a start rule that keeps the late starters' leading zeros out of it, and a score that sets it beside seasonal naive for each client on the same cutoffs. The supplier's day-ahead purchase is a total that [Chapter 7](#why-the-total-needs-a-check) builds from thirty client forecasts. A per-client model needs thirty fits for every window, one for each client. The clients share a daily rhythm, so one model fitted on all of them can learn that rhythm once.

[Chapter 5](#measure-what-each-feature-adds) fitted its model on the eight clients of [`SUBSET8`](#the-case-and-its-data). Fitting one model on all thirty raises three choices that decide whether its score can be trusted: whether to give it a client identifier, how to handle the three late starters (clients whose meters begin partway through the data), and how to score thirty forecasts on one scale. Four examples carry the chapter. Each prints its counts first, so you can check that the model covered the clients it should before you read any error.

## One model for many clients {#one-model-for-many-clients}

[Montero-Manso and Hyndman (2021)](https://doi.org/10.1016/j.ijforecast.2021.03.004), in *Principles and algorithms for forecasting groups of time series: Locality and globality*, show that a global model is no more restrictive than a local one, because both can produce the same forecasts. They compare global methods, which fit one model across a group of series, with local methods, which fit each series on its own. A global model fits one set of parameters to many series in a single pass, so every client contributes to what it learns. Their abstract starts from the view that for groups of similar series, global methods outperform the more established local methods, and it notes that later results in that literature show good performance of global models even in heterogeneous datasets. It also reports that global linear models can give competitive accuracy with two orders of magnitude fewer parameters than local methods. The claims in this paragraph come from that abstract. Bojer and Meldgaard (2020) found that global ensemble models and gradient-boosted trees did well in six Kaggle forecasting competitions ([arXiv:2009.07701](https://arxiv.org/abs/2009.07701)). Those are not the supplier's data, so these sources are a reason to try the approach. They are not evidence about this case. The supplier's clients have the same daily shape and different sizes, so the test has to be run on them.

The data is held in long format: one row per client and hour, with three columns. `unique_id` names the client, `ds` is the hour, and `y` is the kilowatt hours used in that hour. Each row carries its own lags, the readings a day and a week earlier. [Chapter 5](#measure-what-each-feature-adds) found that calendar and holiday features did not lower the error on these eight weeks of history, so this chapter uses lags only, at 24 and 168 hours. Both lags are at least the 24-hour horizon, so neither reads the day being forecast.

The lags cost rows. A lag of 168 hours reads a week back, so the first week of each client's history has no row with every lag available. Chapter 5 showed that `MLForecast` drops such rows from training by default. A client's training rows are therefore fewer than the hours in its history. The forecast itself is unaffected, because each forecast hour reads only readings from before its cutoff.

Clients differ in size, and a squared-error loss over raw kilowatt hours lets the largest set the splits, while the small ones carry little weight. So each client's target is scaled before the fit. The scale is `LocalStandardScaler` from mlforecast 1.1.0. It gives each client its own mean and standard deviation, and the model learns the scaled values:

`z = (y - mean) / standard deviation`

The mean and deviation come from that client's history before the cutoff only, and the forecasts are converted back with the same two numbers. The library's source shows where this happens. `MLForecast.fit` reaches `TimeSeries._fit` in `mlforecast/core.py`, which fits the scaler on each client's history before the cutoff. That history includes the first week, whose rows the lags then drop from training. `TimeSeries.predict` in the same file inverts the scaling. The class is `_BaseLocalScaler` in `mlforecast/target_transforms.py`. [Chapter 5](#measure-what-each-feature-adds) compared the scaled and unscaled targets on `SUBSET8`, and the unscaled model did worse than seasonal naive. This chapter keeps the scaled target and does not repeat that comparison.

`make_forecaster` in the shared module `examples/lib/features.py` builds one `MLForecast` with one `LGBMRegressor`, set by `LGBM_PARAMS`. The model is deterministic, uses one thread and a fixed seed, and runs under LightGBM 4.7.0. The module `examples/lib/panel.py` fits that forecaster once per window, on the panel's history before the window's cutoff. It fills any clock-change hour from that same history, as [Chapter 3](#mark-clock-change-hours-as-missing) does, and returns a forecast for every client.

**Working rule:** Fit one global model when your series share a shape and you must forecast many of them on each window. Scale each series' target with statistics from that window's history only, use only lags at least as long as the horizon, and fit once per window, not once per series. Then score the model per series against a baseline on the same windows, as the sections below do, before you trust its pooled error.

## Identify each client {#identify-each-client}

Once the rows share one table, the model no longer knows which client a row belongs to, unless you tell it. Scaling removes each client's mean and spread, so what remains is mostly the shape of the day. An identifier puts the client in the table as a static categorical feature. The trees can then split on the client and learn that client's own habits. The cost is one more split to learn for each client, and a client with no history has nothing to learn from. A new client therefore needs a refit before the model can forecast it.

The rule for keeping an identifier is the one [Chapter 5](#measure-what-each-feature-adds) sets for every feature: keep it only if it lowers the mean per-client MASE on decision windows that the standard cutoffs do not use. The held-out week runs from Dec 25 to Dec 31, 2014, and it has seven daily cutoffs. The three standard cutoffs, Dec 29 to Dec 31, 2014, are the reported scores, so the decision does not use them, and it does not use Dec 25 to Dec 28, 2014 either. The [decision windows](#choose-on-decision-windows) are four ordinary days before the held-out week: cutoffs on Nov 25, Nov 26, Dec 2 and Dec 3, all in 2014, each forecasting 24 hours. None of their scored hours falls on a Portuguese holiday. The one holiday of 2014 between these windows and the held-out week, Dec 8, 2014, is not among them. The calendar lists no holiday on Dec 1, 2014.

Before the identifier goes into the model, test it on windows the reported scores never touch. The check fits the model twice on each decision cutoff, with and without the identifier, and refuses to start if a scored hour is a holiday or in the held-out week.

Example `client-identifier-check` (Python 3.13.16 · holidays 0.110.dev20261118063242 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.9:

```python
"""Tests whether a client identifier lowers the global model's error on four ordinary decision windows, before the
held-out week, on the book's MASE scale. The point rests on the mean per-client MASE lines and on `identifier kept`."""
from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours, mae_change, panel_windows
from lib.quirks import mask_clock_changes
from lib.scoring import actual_hours, book_scale, report_scores, score_windows
from lib.settings import show

raw = load(ALL30)                                             # all thirty clients, not the eight of SUBSET8
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]        # clock-change hours are set to missing, so the scores leave them out
cutoffs = DECISION_CUTOFFS
actual = actual_hours(df, cutoffs)
holiday_hours = check_decision_hours(actual)  # raises before any fit if a scored hour is a holiday or in the held-out week

plain = panel_windows(df, cutoffs, client_id=False, name="plain")               # the model without the identifier
identified = panel_windows(df, cutoffs, client_id=True, name="identifier")      # the same model, with the client as a feature
models = ["plain", "identifier"]
# the MASE scale reads only the readings before the first decision cutoff, so the scored hours cannot leak into it
scored, per_client = score_windows(actual, plain.merge(identified, on=["unique_id", "ds"], validate="one_to_one"),
                                   models, book_scale(raw, cutoffs[0]))
lowers = per_client["identifier"] < per_client["plain"]
size = raw.groupby("unique_id")["y"].mean().sort_values(ascending=False)   # mean kWh per client, largest first
contrib = mae_change(scored, "plain", "identifier")           # each client's share of the pooled MAE change, kWh; the shares sum to the total

show("first decision cutoff", f"{cutoffs[0]:%Y-%m-%d}")
show("last decision cutoff", f"{cutoffs[-1]:%Y-%m-%d}")
show("clients", scored["unique_id"].nunique())
show("windows", len(cutoffs))
show("scored hours", len(scored))
show("decision hours on a holiday", holiday_hours)
report_scores(scored, per_client, models)
show("clients where the identifier lowers MASE", int(lowers.sum()))
show("of the 15 largest clients, where the identifier lowers MASE", int(lowers[size.index[:15]].sum()))
show("of the 15 smallest clients, where the identifier lowers MASE", int(lowers[size.index[-15:]].sum()))
show("largest client", size.index[0])
show("pooled MAE change from the largest client, kWh", contrib[size.index[0]])
show("pooled MAE change, all clients, kWh", contrib.sum())
# the decision rule keeps the identifier only if the mean per-client MASE is lower, not the pooled MAE
show("identifier kept", "yes" if per_client["identifier"].mean() < per_client["plain"].mean() else "no")
```

Output:

```text
first decision cutoff: 2014-11-25
last decision cutoff: 2014-12-03
clients: 30
windows: 4
scored hours: 2880
decision hours on a holiday: 0
MAE plain: 70.72
MAE identifier: 66.81
RMSE plain: 316.50
RMSE identifier: 303.68
mean MASE plain: 0.77
mean MASE identifier: 0.75
clients where the identifier lowers MASE: 23
of the 15 largest clients, where the identifier lowers MASE: 10
of the 15 smallest clients, where the identifier lowers MASE: 13
largest client: MT_370
pooled MAE change from the largest client, kWh: -3.80
pooled MAE change, all clients, kWh: -3.92
identifier kept: yes
```

The identifier lowers the mean per-client MASE, from 0.77 to 0.75, and it lowers the MASE of 23 of the thirty clients.

On these windows the pooled MAE falls too, from 70.72 kWh to 66.81 kWh. The two errors weigh clients differently, because the pooled MAE is weighted toward the largest.

The pooled change of -3.92 kWh is almost all from one client, MT_370, which accounts for -3.80 kWh of it.

The per-client MASE gives every client the same weight, and the identifier helps across sizes. It lowers the MASE of 10 of the fifteen largest clients and of 13 of the fifteen smallest. It does not help only the large clients.

The printed verdict is yes, so the identifier is kept and the final model uses it. The margin is small. Other windows could give the opposite sign by a similar small amount, so the verdict is close and depends on the windows. A reader with other windows should measure it again before trusting it.

The identifier has a cost at the standard cutoffs. There, the final model's mean per-client MASE is 0.91 with the identifier, against 0.98 without it, but its pooled MAE is 122.81 kWh, against 119.03 kWh without it. Chapter 7 has to check its total against that. The rest of the chapter uses the model with the identifier.

**Working rule:** Treat a client identifier as one more feature under [Chapter 5's rule](#measure-what-each-feature-adds): keep it only if it lowers the mean per-client MASE on the decision windows, with the pooled MAE beside it. If the decision is close, say so, and measure it again on other windows. If the identifier wins, write down its cost: a new client has no learned split until it has history, and the model must be refitted before it can forecast that client.

## Apply the start rule to every client {#apply-the-start-rule-to-every-client}

A series begins at its first reading. Before that, the meter reports zeros, and those zeros are not low use. [Chapter 4](#meet-the-late-starters) met this for one client. With thirty clients, three are late starters. `MT_039` first reads on 2013-10-03, `MT_179` on 2013-12-20, and `MT_115` on 2014-01-14. A model fitted on their leading zeros learns a level near zero for them. The start rule drops every reading before a client's first reading. It finds that reading in the rows before the cutoff only.

The rule refuses a cutoff in two cases only: a client has no non-zero reading before the cutoff, or it has fewer than 48 hours of history since its first reading. It does not skip the client, because a skipped client leaves the total short. The rule does not catch a gap or a run of zeros in the middle of a series, and a meter replaced under the same id passes too, because its zeros are not leading. The scale catches a gap, because it refuses a series that is not one unbroken hourly series. Nothing in the forecast checks for one, so a gap there shows only as fewer training rows.

The leak check asks whether the rule reads only the past and refuses the right cutoffs. It runs nine cutoffs, refused or not, and poisons each from the cutoff on, once with zeros and once with a value no meter could record. The history must not change, and every accepted cutoff must hold all thirty clients.

Example `start-rule-leak-check` (Python 3.13.16 · holidays 0.110.dev20261118063242 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.9:

```python
"""Checks that the start rule reads only rows before each cutoff, refuses the cutoffs the data's flag predicts, and
removes only leading zeros, on nine cutoffs. The same checks run on a deliberately broken history function, and each
must fail there; the point rests on the refused, changed and missing counts. The checks are start_rule_checks in lib/panel.py."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30, FEBRUARY_CUTOFFS, leaky_history, panel_history, start_rule_checks
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
# nine cutoffs: three around MT_179's and MT_115's first readings (refused), the February cutoffs and the standard cutoffs
CHECKED = pd.DatetimeIndex(["2013-12-15", "2014-01-01", "2014-01-15", *FEBRUARY_CUTOFFS, *EVAL_CUTOFFS])


def report(prefix, r):
    show(f"{prefix}cutoffs checked", len(CHECKED))
    show(f"{prefix}cutoffs refused by the start rule", r["refused"])
    show(f"{prefix}cutoffs expected to be refused, from the flag", r["expected"])
    show(f"{prefix}cutoffs where the refusal differs from the flag", r["mismatch"])
    show(f"{prefix}cutoffs accepted", r["accepted"])
    show(f"{prefix}accepted cutoffs with a client missing from the history", r["missing"])
    show(f"{prefix}cutoffs whose history changes when the future is poisoned", r["changed"])


# the book's history function, with the count of rows the rule removes switched on
real = start_rule_checks(raw, CHECKED, panel_history, removed_rows=True)
report("", real)
show("rows the start rule removes, accepted cutoffs", real["removed"])
show("removed rows that are not zero", real["removed_nonzero"])
# the deliberately broken history, which reads each first reading from the whole series, must fail every check
report("broken version, ", start_rule_checks(raw, CHECKED, leaky_history))
```

Output:

```text
cutoffs checked: 9
cutoffs refused by the start rule: 3
cutoffs expected to be refused, from the flag: 3
cutoffs where the refusal differs from the flag: 0
cutoffs accepted: 6
accepted cutoffs with a client missing from the history: 0
cutoffs whose history changes when the future is poisoned: 0
rows the start rule removes, accepted cutoffs: 2064
removed rows that are not zero: 0
broken version, cutoffs checked: 9
broken version, cutoffs refused by the start rule: 1
broken version, cutoffs expected to be refused, from the flag: 3
broken version, cutoffs where the refusal differs from the flag: 2
broken version, cutoffs accepted: 8
broken version, accepted cutoffs with a client missing from the history: 2
broken version, cutoffs whose history changes when the future is poisoned: 2
```

The real rule passes all three checks. Its refusals match the data's own flag, which uses each first reading and the 48-hour rule: the rule refuses 3 of the nine cutoffs, the flag predicts 3, and 0 cutoffs differ from it.

Poisoning the future changes no history. Its history changes at 0 cutoffs, and 0 accepted cutoffs are missing a client.

The rule removes leading zeros and nothing else. Across the accepted cutoffs it drops 2064 rows, and 0 of them are not zero.

The same checks run on a deliberately broken version, which reads each first reading from the whole series, the leak the checks are written for. It fails each of them. Its refusals differ from the flag at 2 cutoffs, its history changes at 2, and 2 accepted cutoffs drop a client without a message. So a pass on the real rule means something.

The model runs with the start rule and without it, on the standard cutoffs and then the February cutoffs. The counts that differ, and each run's error, show what the rule does.

Example `global-model-raw-starts` (Python 3.13.16 · holidays 0.110.dev20261118063242 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.9:

```python
"""Runs the global model with the start rule and without it, on the February cutoffs, where a late starter's zeros enter
the history, and on the standard cutoffs, where the rule changes no row. The point rests on the February mean MASE lines
and the count of forecast hours that differ; the scale lines compare the book's scale with a labelled counterfactual."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.panel import (ALL30, FEBRUARY_CUTOFFS, IDENTIFIER_KEPT, LATE_STARTERS, late_starter_facts, mae_by_group,
                       mase_by_run, scale_facts, with_and_without_start_rule)
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]        # clock-change hours are set to missing, so the scores leave them out
for label, value in late_starter_facts(raw, df).items():
    show(label, value)

standard = pd.to_datetime(EVAL_CUTOFFS)                       # the three standard cutoffs
# two runs of the same model on the same cutoffs, differing only in their histories
scored = with_and_without_start_rule(df, standard, client_id=IDENTIFIER_KEPT)
# compared with isclose, so a rounding difference between two runs does not count as a changed forecast
show("forecast hours that differ, standard", int((~np.isclose(scored["start"], scored["raw"])).sum()))

# the February cutoffs, where the zeros of MT_115 and MT_179 enter the history
feb = with_and_without_start_rule(df, FEBRUARY_CUTOFFS, client_id=IDENTIFIER_KEPT)
show("scored hours, february", len(feb))
show("forecast hours that differ, february", int((~np.isclose(feb["start"], feb["raw"])).sum()))
for model in ["start", "raw"]:
    for group, value in mae_by_group(feb, model).items():
        show(f"MAE {group}, {model}, february", value)
# both runs on one scale, read from the first February cutoff
feb_mase = mase_by_run(raw, feb, ["start", "raw"])
show("clients in MASE, february", int(feb_mase["start"].notna().sum()))
for uid in LATE_STARTERS:
    show(f"MASE {uid}, start, february", feb_mase.loc[uid, "start"])
    show(f"MASE {uid}, raw, february", feb_mase.loc[uid, "raw"])
for run in ["start", "raw"]:
    show(f"mean MASE, {run}, february", feb_mase[run].mean())

# 'counterfactual raw' keeps the zeros before each first reading, a scale the book does not use; 'start rule' is the book's
for label, value in scale_facts(raw, standard, IDENTIFIER_KEPT).items():
    show(label, value)
```

Output:

```text
first reading MT_039: 2013-10-03
first reading MT_115: 2014-01-14
first reading MT_179: 2013-12-20
zero share of history MT_115, 2014-02-01: 68
zero share of history MT_179, 2014-02-01: 23
zero share of history MT_115, 2014-02-15: 43
zero share of history MT_179, 2014-02-15: 0
zero share of history MT_115, 2014-02-28: 20
zero share of history MT_179, 2014-02-28: 0
forecast hours that differ, standard: 0
scored hours, february: 2160
forecast hours that differ, february: 2160
MAE late starters, start, february: 4.60
MAE other clients, start, february: 77.53
MAE MT_039, start, february: 4.64
MAE MT_115, start, february: 4.62
MAE MT_179, start, february: 4.54
MAE late starters, raw, february: 4.60
MAE other clients, raw, february: 77.95
MAE MT_039, raw, february: 4.57
MAE MT_115, raw, february: 4.68
MAE MT_179, raw, february: 4.53
clients in MASE, february: 30
MASE MT_039, start, february: 0.78
MASE MT_039, raw, february: 0.77
MASE MT_115, start, february: 0.90
MASE MT_115, raw, february: 0.91
MASE MT_179, start, february: 0.54
MASE MT_179, raw, february: 0.54
mean MASE, start, february: 0.70
mean MASE, raw, february: 0.71
MASE scale MT_039, start rule: 5.21
MASE scale MT_039, counterfactual raw: 3.28
MASE scale MT_115, start rule: 4.58
MASE scale MT_115, counterfactual raw: 2.22
MASE scale MT_179, start rule: 5.91
MASE scale MT_179, counterfactual raw: 3.04
mean MASE global, counterfactual raw scale, standard cutoffs: 1.01
mean MASE global, book scale, standard cutoffs: 0.91
```

At the standard cutoffs the rule matters less than the late starters might suggest. The three standard cutoffs have 8 weeks of history, reaching back to early November, and no client's history in that window holds a zero from before its first reading. So the rule changes no training row there, and 0 of the 2160 forecast hours change. The rule still changes the score through the MASE scale.

The February cutoffs, which Chapter 4 used for `MT_115`, are where the zeros enter the history. `MT_115`'s history is 68 percent zeros on Feb 1, 2014, 43 percent on Feb 15 and 20 percent on Feb 28. `MT_179`'s history is 23 percent zeros on Feb 1 and none after.

Here the forecasts change, because one model learns from all thirty clients at once: 2160 of the 2160 forecast hours in these three windows differ. Both runs are scored on the one book scale, read from Feb 1, 2014, so only the histories differ. The mean MASE is 0.70 with the rule and 0.71 without it.

Each late starter's MASE moves very little, and the direction is mixed. `MT_039` scores 0.78 with the rule and 0.77 without it, and `MT_115` scores 0.90 with the rule and 0.91 without.

`MT_179` scores 0.54 with the rule and 0.54 without it, the same to two decimals.

The other 27 clients' MAE moves from 77.95 kWh without the rule to 77.53 kWh with it. The effect is small and mixed, and three windows are too few to call it. We keep the rule because the zeros are not demand, and because the scale depends on it.

You could instead mark the zeros as missing, as the clock rule does for the two clock-change hours in [Chapter 3](#mark-clock-change-hours-as-missing). That would be the wrong fix for this data. A zero before a first reading is the meter being silent, not a reading that is missing, and a missing value would still be a row the model learns from. The start rule removes the rows instead, and its check is simple to state: it removes only rows before the first reading, and every one of them is zero.

**Working rule:** Apply the start rule to every series that has leading zeros, and find each first reading from the rows before the cutoff. When the rule refuses a cutoff, stop the run and name the client and the cutoff. Do not fill the zeros, and do not publish a panel with a client missing. Judge the rule by the scale and by the windows where zeros enter the history, and expect the MAE effect to be small and mixed.

## Score thirty clients on the same cutoffs {#score-thirty-clients-on-the-same-cutoffs}

The three standard cutoffs are Dec 29 to Dec 31, 2014, each at 00:00 on that day, with 24 hours forecast from each. For thirty clients that is 72 scored hours per client. Seasonal naive is the baseline [Chapter 2](#three-baselines-to-beat) set. It takes each cutoff's own history, the 8 weeks before it, and copies the last day's readings forward. At the standard cutoffs no client's history holds a leading zero, so the global model and seasonal naive read the same readings. The comparison is fair because the inputs match, not because the methods are alike.

The headline is the mean per-client MASE, the measure [Chapter 2](#scale-errors-with-mase) defines. The book uses one scale per client per backtest, the rule [Chapter 2](#take-the-mase-scale-from-history) sets, and the function `book_scale` in `examples/lib/scoring.py` builds it. The scale is the mean absolute change between each reading and the reading one day earlier, taken over every reading before the first scored cutoff. A late starter is counted from its first reading, and the clock-change readings are masked out. A client with no non-zero reading before the cutoff has no scale, so it is left out of MASE and reported, not treated as an error. Because the scale reads only readings before the scored windows, it is known at every cutoff and cannot leak. Each client counts once in the mean, so one large client cannot set the headline. The pooled MAE and RMSE follow as second lines. They show the error in kilowatt hours that the supplier pays, and they are weighted toward the large clients.

The scale is part of the score. `MT_115`'s scale is 2.22 kWh if the zeros before its first reading are kept, and 4.58 kWh with the book's rule, which counts it from its first reading.

`MT_039` and `MT_179` move the same way. `MT_039`'s scale rises from 3.28 to 5.21 kWh, and `MT_179`'s from 3.04 to 5.91 kWh.

On the standard cutoffs the same forecasts score a mean MASE of 1.01 with the scale that keeps the zeros, and 0.91 with the book's scale. That difference is the scale, not the model. A score computed with a different scale rule is not comparable with one computed with the book's rule, so every score should record the rule it used.

The score below sets the global model beside seasonal naive on the three standard cutoffs.

Example `global-model-thirty-clients` (Python 3.13.16 · holidays 0.110.dev20261118063242 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.9:

```python
"""Scores one global LightGBM model, with the identifier that client-identifier-check kept, against seasonal naive on the
three standard cutoffs, per client on the book's MASE scale. The point rests on the mean per-client MASE lines; the model
without the identifier is printed for reference only."""
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows
from lib.baselines import SEASON
from lib.electricity import load
from lib.panel import ALL30, IDENTIFIER_KEPT, panel_windows
from lib.quirks import mask_clock_changes
from lib.scoring import actual_hours, book_scale, left_out_facts, report_scores, score_windows
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]        # clock-change hours are set to missing, so the scores leave them out
cutoffs = pd.to_datetime(EVAL_CUTOFFS)                        # the three standard cutoffs, Dec 29 to Dec 31, 2014
actual = actual_hours(df, cutoffs)

# seasonal naive from each cutoff's own history: the baseline of Chapter 2
naive = forecast_windows(StatsForecast(models=[SeasonalNaive(season_length=SEASON)], freq="h", n_jobs=1), df, cutoffs)
global_fc = panel_windows(df, cutoffs, client_id=IDENTIFIER_KEPT)   # the identifier setting that client-identifier-check kept
plain_fc = panel_windows(df, cutoffs, client_id=False, name="plain")  # the same model without the identifier, for reference
forecasts = naive.merge(global_fc, on=["unique_id", "ds"], validate="one_to_one").merge(
    plain_fc, on=["unique_id", "ds"], validate="one_to_one")
models = ["SeasonalNaive", "global", "plain"]
# the book's scale, read from the readings before the first cutoff only
scored, per_client = score_windows(actual, forecasts, models, book_scale(raw, cutoffs[0]))
beats = per_client["global"] < per_client["SeasonalNaive"]    # per client: True where the global model's MASE is lower

show("clients scored", scored["unique_id"].nunique())
show("windows", len(cutoffs))
show("scored hours", len(scored))
# a client with no non-zero reading before the first cutoff is left out of MASE, and is not an error
for label, value in left_out_facts(raw, df, cutoffs[0]).items():
    show(label, value)
show("clients in MASE", per_client["global"].notna().sum())
show("clients where global beats seasonal naive", int(beats.sum()))
show("clients where seasonal naive wins", ", ".join(sorted(per_client.index[~beats])))
report_scores(scored, per_client, models)
```

Output:

```text
clients scored: 30
windows: 3
scored hours: 2160
clients left out of MASE: 0
clients with no reading before 2013-12-15, check: 2
clients with any row before 2013-12-15, broken count: 30
clients in MASE: 30
clients where global beats seasonal naive: 23
clients where seasonal naive wins: MT_001, MT_128, MT_141, MT_179, MT_217, MT_268, MT_294
MAE SeasonalNaive: 148.26
MAE global: 122.81
MAE plain: 119.03
RMSE SeasonalNaive: 780.48
RMSE global: 678.81
RMSE plain: 657.63
mean MASE SeasonalNaive: 1.18
mean MASE global: 0.91
mean MASE plain: 0.98
```

The example scores 30 clients on 3 windows, 2160 scored hours, and it counts 0 clients left out of MASE, which is zero: every client has a non-zero reading before the first cutoff, so every client is in the MASE table.

The count is only as good as its rule. At a cutoff of Dec 15, 2013, 2 clients have no reading yet, and counting any row before the cutoff would give 30, which reports no gap.

One global model beats seasonal naive on these cutoffs, for most clients and in total: its mean per-client MASE is 0.91 against 1.18, and it wins for 23 of the thirty clients. It loses for MT_001, MT_128, MT_141, MT_179, MT_217, MT_268, MT_294, and those clients are the first place to look when the model is refreshed.

The pooled figures point the same way. The MAE is 122.81 kWh against 148.26 kWh, and the RMSE is 678.81 kWh against 780.48.

The model without the identifier, printed for reference, has a mean MASE of 0.98 and an MAE of 119.03 kWh, which is the trade-off the [identifier section](#identify-each-client) describes.

The printed figures are means and counts, and a mean can hide one client that is far worse than the rest. When a figure changes, open the per-client table first.

The chapter does not explain why seasonal naive wins for those clients, and that is a reason not to report only the pooled figure. The result covers three windows in one week of one season, so it describes these cutoffs, not every day of the year. The longer test is the seven-window held-out week, which the rolling example in [Chapter 10](#log-every-forecast-before-actuals) uses.

**Working rule:** Score a global model per client on the same cutoffs as the baseline, with the MASE scale fixed before the first scored cutoff. Report the mean per-client MASE beside seasonal naive, and print the counts of clients and scored hours so a reader can check them. State any client left out of MASE and why. Read the pooled MAE and RMSE as the cost in kilowatt hours, not as the measure of model quality.

## Budget the run time {#budget-the-run-time}

A backtest costs fits, and the count is what to check before you run one. A per-client model is fitted once for each client, each window and each method, so the count is clients times windows times methods. Thirty clients over three windows is ninety fits for one per-client method. A global model is fitted once for each window and method, however many clients it covers, so the same three windows cost three fits. More clients make each global fit larger, but they do not add fits.

The book sets a subset rule for the expensive per-client methods. [`SUBSET8`](#the-case-and-its-data) is the eight-client subset that [Chapter 4](#fit-exponential-smoothing) runs its per-client statistical models on. A global model covers all thirty in one fit, so it runs on all thirty clients, as `ALL30`. The subsets are fixed for the whole book, so a number in one chapter can be set beside the next. The window count follows the same logic. Expensive methods use three windows, and cheap methods can use more. Each window of the identifier check costs two global fits, one with the identifier and one without, so its four windows cost eight fits.

The two kinds of cost move differently when the number of clients grows. A per-client method gets more fits, one for each new client. A global model gets bigger fits, because each one reads more rows, and it keeps the same number of fits.

The book does not quote timings. The examples run with one thread, so their output repeats on the machine that recorded the book's outputs, and that choice costs run time. A time depends on the machine, and a reader's machine may differ. Count the fits, not the seconds.

**Working rule:** Before you run a backtest, count its fits: clients times windows times methods for a per-client method, and windows times methods for a global one. If the count is over budget, cut the subset or the window count, never the scored windows, and write the cut down beside the score. Then a reader can compare like with like.

## What goes wrong in production {#what-goes-wrong-ch6}

A run can stop. A client with no non-zero reading before a cutoff, or with under 48 hours of history since its first reading, makes the start rule refuse that cutoff. The rule raises an error instead of skipping the client, because a skipped client leaves the total short, and [Chapter 7](#sum-the-client-forecasts) sums the clients to make the total. In production the run should stop, name the client and the cutoff, and wait for a person. The leak check shows the same refusals in the book's data.

One model moves every client. At the February cutoffs, the late starters' zeros changed 2160 forecast hours, and the other 27 clients' MAE moved as well, as the [start-rule section](#apply-the-start-rule-to-every-client) shows. Any change to one client's history, to a rule, or to a feature changes forecasts across the panel. After any change, check every client, not only the one you changed.

The scale is part of the score. The same forecasts score a mean MASE of 1.01 or 0.91, depending on whether the scale keeps the zeros before a first reading. The [scoring section](#score-thirty-clients-on-the-same-cutoffs) gives the scales. Record the rule with every score, and treat a change to the rule as a change to the score.

The decisions can drift. The identifier decision rests on four ordinary windows that lie outside the held-out week, and its verdict is close. When clients join, leave or change size, the decision should be made again.

A missing client does not appear as an error in the table. A panel of twenty-nine clients is still a valid table, and a forecast of it still looks like a forecast. A run that scores fewer clients or hours than expected, or a count of clients where the global model beats seasonal naive that changes sharply between runs, is a reason to stop. So is a per-client MASE that jumps for one client while the pooled MAE stays flat.

**Working rule:** Print and check the counts (clients, windows, scored hours, refused cutoffs, clients left out of MASE) on every refresh, before any score is read. Then report the mean per-client MASE beside seasonal naive. Stop the run on any refusal, and do not publish a total built from a short panel.

## Decisions this chapter made {#decisions-ch6}

[Chapter 7](#why-the-total-needs-a-check) starts from what this chapter hands over: thirty client forecasts for each standard cutoff, made by one model with the client identifier and the start rule applied, and scored on the book's one MASE scale. The identifier is kept by the decision in `client-identifier-check`, and `examples/lib/panel.py` holds that verdict in `IDENTIFIER_KEPT`. The pooled error at these cutoffs is worse with the identifier, so Chapter 7 should check the total before it relies on the client forecasts.

- One global LightGBM model covers all thirty clients, with lags 24 and 168, no calendar or holiday features, and each client's target scaled from that window's history only, the scaling [Chapter 5](#measure-what-each-feature-adds) settles on.
- A client identifier is kept. The decision used four ordinary windows, from Nov 25 to Dec 3, 2014, outside the held-out week and without a Portuguese holiday, as the book's rule for choosing a setting requires. Mean MASE on those windows moves from 0.77 to 0.75. The verdict is close, as [the identifier section](#identify-each-client) shows.
- The start rule applies to every client. It refuses a cutoff it cannot start, instead of skipping the client.
- Clock-change hours in each panel history are filled from that history only, so a rolling window across a clock change is fitted, not refused. Chapter 10's rolling windows depend on this.
- The headline is the mean per-client MASE over all thirty clients, on the book's one scale (set in [Chapter 2](#take-the-mase-scale-from-history) and computed by `book_scale`), beside seasonal naive on the same cutoffs. A client with no non-zero reading before the cutoff is left out of MASE and reported. The pooled MAE and RMSE follow as second lines. No client is left out at the standard cutoffs, because each has a reading before the first cutoff.
- The model runs on one thread with a fixed seed, so its output repeats on the machine that recorded the book's outputs. The book has not tested other machines.
