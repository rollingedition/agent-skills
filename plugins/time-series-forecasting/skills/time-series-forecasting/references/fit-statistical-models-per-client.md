---
title: "Time Series Forecasting"
chapter: "Fit a statistical model for each client"
chapter_id: fit-statistical-models-per-client
book: time-series-forecasting
edition: 2026.11.13
verified: 2026-11-20
edition_code: AVAY-NYWJ
canonical: https://rollingedition.com/time-series-forecasting/fit-statistical-models-per-client
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Fit a statistical model for each client,” chapter 4 of Time Series Forecasting, Edition 2026.11.13, examples passed Nov 20, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/fit-statistical-models-per-client. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Fit a statistical model for each client

Here you fit AutoETS and a fixed seasonal ARIMA for each client over the same backtest, score both against seasonal naive, and learn to start a late-starting client at its first reading. The chapter assumes the baselines and backtests of the two chapters before it.

Each of the supplier's clients needs its own day-ahead forecast, and [Chapter 2](#beat-the-naive-baselines)'s seasonal naive gives every one of them the same answer: the same hour yesterday. That rule keeps no estimate of a client's level or its trend, and the clients differ in both. So this chapter fits a statistical model for each client, and asks whether the extra work pays.

## Why a statistical model comes next {#why-a-statistical-model-comes-next}

[Chapter 2](#beat-the-naive-baselines) set the bar. [Seasonal naive](#forecast-with-seasonal-naive) forecasts each hour as the same hour yesterday, and the scaled error, MASE, compares clients with different loads on one scale. [Chapter 3](#backtest-without-looking-ahead) backtested that forecast over many cutoffs. A [cutoff](#the-case-and-its-data) is the time a forecast is made, and its history ends there. A [window](#the-case-and-its-data) is one cutoff and the 24 hours after it, which is the horizon. Each window's history ends at its cutoff, so no hour is forecast with data from its own day.

A statistical model adds to that loop. A series has a state. The level of a series is its typical reading, the trend is the slow drift of the level, the season is the daily shape of the load, and what none of these explain is error. A statistical model holds an estimate of each part of the state of a series, updates the estimates as each reading arrives, and projects them over the horizon. Seasonal naive has no such state. It copies yesterday, so it gets a client's level only as well as yesterday did.

A per-client model is one fit for each client, on that client's history alone, so the cost is one fit per client per window. The subset this chapter uses, [`SUBSET8`](#the-case-and-its-data), has eight clients. Over the book's three standard cutoffs, Dec 29 to Dec 31, 2014, the last three days of the held-out week and the windows every later chapter reports, that is 24 fits for each model. The code runs the fits in one worker (`n_jobs=1`), which keeps the output identical from run to run. Every model in this chapter gets the same three cutoffs and the same 1,344 hours of history before each one. The cutoffs fall in the held-out week, and the subset holds the one late starter a later section needs.

**Working rule:** Fit one model per client only after a baseline and a backtest are in place. Count the fits before you choose the number of windows: clients, times windows, times refits if you run the model every day. Use the same cutoffs and history for every model in a comparison. Otherwise the comparison measures the windows, not the models.

## Fit exponential smoothing {#fit-exponential-smoothing}

Seasonal naive keeps only yesterday, so the first candidate keeps a level instead. Exponential smoothing moves its level toward each new reading. The simplest form updates the level as `level_t = alpha * y_t + (1 - alpha) * level_(t-1)`. The constant alpha, between 0 and 1, sets how fast the level follows the data. The forecast for every hour of the horizon is the last level. Recent readings count for more than older ones, and the weights fall off with age.

ETS, for error, trend and season, extends the simplest form of exponential smoothing. Each part is chosen from a short list. The trend can be none, additive or damped. The error can be additive or multiplicative, and the season can be none, additive or multiplicative. A name such as ETS(A,N,A) reads in that order: additive error, no trend, additive season. ETS(M,Ad,M) has a multiplicative error, a damped trend and a multiplicative season.

[AutoETS](#forecast-with-a-statistical-model) chooses the ETS form for you. Its default criterion is [AICc](#forecast-with-a-statistical-model), the corrected Akaike information criterion, which charges a model for each parameter and corrects for small samples, as the `AutoETS` docstring in statsforecast 2.1.1 (`statsforecast/models.py`) says. Two of its defaults matter for hourly demand. The season length defaults to 1, which means no season at all, and the model gives no warning when you leave it that way. The `model` argument defaults to `"ZZZ"`, which lets the model choose all three parts. For hourly demand with a daily pattern, the call sets `season_length=24`.

Which form does AutoETS pick for each client, and do its forecasts beat seasonal naive? The lines it prints answer both.

Example `autoets-subset-backtest` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.13:

```python
"""Backtest AutoETS and seasonal naive for the eight clients of SUBSET8 over the three standard cutoffs, and score both.
The fits lines count the forms AutoETS chose, and the MASE and coverage lines are the scores the comparison table quotes."""
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS, SeasonalNaive

from lib.scoring import book_scale
from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, HORIZON, SEED, SUBSET8, show
from lib.subsets import score_clients, show_client_lines
np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
masked = mask_clock_changes(load(SUBSET8))                  # clock-change hours become NaN, so they are never scored; filled_history fills them from their neighbours before each fit
scale = book_scale(load(SUBSET8), EVAL_CUTOFFS[0])        # MASE scale: rows before the first cutoff, from each client's first reading
# season_length=24 for hourly demand; the default of 1 would mean no season at all. n_jobs=1 keeps the output the same from run to run.
sf = StatsForecast(models=[AutoETS(season_length=24), SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
parts, forms, by_client = [], Counter(), defaultdict(list)
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])   # the eight weeks before c, clock hours filled from them
    part = sf.predict(h=HORIZON, level=[95])                          # level=[95] asks for the 95% interval the coverage line scores
    # the first forecast hour must be the cutoff itself, or the window is misaligned
    if part["ds"].min() != c:
        raise ValueError(f"forecast for {c:%Y-%m-%d} does not start at the cutoff")
    parts.append(part)
    for i, uid in enumerate(sf.uids):
        form = sf.fitted_[i, 0].model_["method"]                    # model 0 is AutoETS; its method name is the form, such as ETS(A,N,A)
        forms[form] += 1
        by_client[uid].append(form)
forecasts = pd.concat(parts, ignore_index=True)
summary, per_client = score_clients(forecasts, masked, ["AutoETS", "SeasonalNaive"], scale, interval_model="AutoETS")
show("horizon hours", HORIZON)
show("windows", len(parts))
for form, n in sorted(forms.items()):
    show(f"fits that chose {form}", n)
# the form reads ETS(error,trend,season): a multiplicative part is an M in any of the three slots
show("fits with a multiplicative part", sum(n for form, n in forms.items() if "M" in form[4:-1].split(",")))
for label, value in summary.items():
    show(label, value, digits=3 if label.startswith("coverage") else 2)   # coverage is a share, to three decimals; the rest are kWh or ratios
show("clients where AutoETS has lower MASE", int((per_client["AutoETS"] < per_client["SeasonalNaive"]).sum()))
show_client_lines(by_client, per_client, ["AutoETS", "SeasonalNaive"])
```

Output:

```text
horizon hours: 24
windows: 3
fits that chose ETS(A,Ad,A): 1
fits that chose ETS(A,N,A): 8
fits that chose ETS(A,N,N): 9
fits that chose ETS(M,Ad,M): 2
fits that chose ETS(M,N,A): 3
fits that chose ETS(M,N,M): 1
fits with a multiplicative part: 6
clients: 8
scored hours per client: 72
MAE AutoETS: 362.11
RMSE AutoETS: 537.20
MASE AutoETS: 1.30
MAE SeasonalNaive: 423.68
RMSE SeasonalNaive: 591.25
MASE SeasonalNaive: 1.16
coverage 95 AutoETS: 0.910
clients where AutoETS has lower MASE: 4
forms MT_014, one per cutoff: ETS(A,N,N) ETS(A,N,N) ETS(A,N,N)
MASE MT_014 AutoETS: 1.18
MASE MT_014 SeasonalNaive: 0.97
forms MT_064, one per cutoff: ETS(A,N,N) ETS(A,N,N) ETS(A,N,N)
MASE MT_064 AutoETS: 2.32
MASE MT_064 SeasonalNaive: 1.08
forms MT_115, one per cutoff: ETS(M,N,A) ETS(M,N,A) ETS(M,N,A)
MASE MT_115 AutoETS: 0.95
MASE MT_115 SeasonalNaive: 1.31
forms MT_166, one per cutoff: ETS(A,Ad,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_166 AutoETS: 1.18
MASE MT_166 SeasonalNaive: 1.29
forms MT_217, one per cutoff: ETS(M,N,M) ETS(M,Ad,M) ETS(M,Ad,M)
MASE MT_217 AutoETS: 1.76
MASE MT_217 SeasonalNaive: 1.25
forms MT_268, one per cutoff: ETS(A,N,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_268 AutoETS: 0.94
MASE MT_268 SeasonalNaive: 0.89
forms MT_319, one per cutoff: ETS(A,N,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_319 AutoETS: 1.11
MASE MT_319 SeasonalNaive: 1.26
forms MT_370, one per cutoff: ETS(A,N,N) ETS(A,N,N) ETS(A,N,N)
MASE MT_370 AutoETS: 0.96
MASE MT_370 SeasonalNaive: 1.25
```

The chosen form changes from client to client, and for some clients from one cutoff to the next. Across the 24 fits, AutoETS chose ETS(A,N,N), with no season, for 9 of them, and ETS(A,N,A), with an additive season, for 8. ETS(A,Ad,A), a damped trend with an additive season, came up in 1 of the fits. The other fits used a multiplicative part, in the error, the season or both. The lines under the totals give each client's three forms. Three clients, `MT_014`, `MT_064` and `MT_370`, take the flat form at all three cutoffs. `MT_014` is the lead client, the one [Chapter 1](#forecast-tomorrows-demand) met.

A flat form winning looks odd when the seasonal form contains it. ETS(A,N,N) is ETS(A,N,A) with the seasonal part switched off, so the best seasonal fit cannot have a lower likelihood than the flat fit on the same history. Fitting both forms on each of the 24 windows shows whether that happens.

Example `flat-form-check` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.13:

```python
"""For each subset window, fit the flat form ETS(A,N,N) and the additive-season form ETS(A,N,A) on the same history, and count where the seasonal fit has the lower likelihood.
The two counts printed last are the ones the prose quotes."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, SEED, SUBSET8, show

np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
masked = mask_clock_changes(load(SUBSET8))
windows = seasonal_lower_loglik = seasonal_higher_aicc = 0
for c in pd.to_datetime(EVAL_CUTOFFS):
    hist = filled_history(masked, c)[["unique_id", "ds", "y"]]
    # ANN is additive error, no trend, no season: the flat form. ANA is the same with an additive season.
    sf = StatsForecast(models=[AutoETS(model="ANN", season_length=24, alias="flat"),
                               AutoETS(model="ANA", season_length=24, alias="seasonal")], freq="h", n_jobs=1)
    sf.fit(df=hist)
    for i in range(len(sf.uids)):
        flat = sf.fitted_[i, 0].model_                          # models are fitted in the order listed: 0 is the flat fit
        seasonal = sf.fitted_[i, 1].model_                      # 1 is the seasonal fit
        windows += 1
        # ANA contains ANN, so a lower seasonal likelihood points to a fit that stopped short of its best
        seasonal_lower_loglik += int(seasonal["loglik"] < flat["loglik"])
        # AICc charges each parameter, so this count can differ from the likelihood count
        seasonal_higher_aicc += int(seasonal["aicc"] > flat["aicc"])
show("windows", windows)
show("seasonal fit has the lower log-likelihood", seasonal_lower_loglik)
show("seasonal fit has the higher AICc", seasonal_higher_aicc)
```

Output:

```text
windows: 24
seasonal fit has the lower log-likelihood: 9
seasonal fit has the higher AICc: 9
```

The seasonal fit loses on likelihood, not only on AICc. Its log-likelihood is lower in 9 of the 24 windows, and its AICc is higher in 9. Those are the same nine windows in which the default run chose the flat form. AICc charges a model for each parameter, and the seasonal form has 24 more. That charge adds to the gap; it does not cause it, because the seasonal fit's likelihood is already lower before any charge. The seasonal fit most likely stopped short of its best value, and the flat form won by default. The book does not chase the optimiser; it tests the choice with a forced season.

[Chapter 1](#forecast-with-a-statistical-model) forced an additive season on the lead client, with `model="ZZA"`, and seasonal naive still had the lower error there. Does that hold across all eight? The forced run covers the same eight clients, beside the default.

Example `autoets-forced-season-backtest` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.13:

```python
"""Backtest AutoETS with the season forced to additive (model ZZA) and seasonal naive, for the eight clients of SUBSET8 over the three standard cutoffs.
The ZZA lines are the forced-season scores that the comparison table and the forced-season paragraph quote."""
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS, SeasonalNaive

from lib.scoring import book_scale
from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, HORIZON, SEED, SUBSET8, show
from lib.subsets import score_clients, show_client_lines
np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
masked = mask_clock_changes(load(SUBSET8))                  # clock-change hours become NaN, so they are never scored; filled_history fills them from their neighbours before each fit
scale = book_scale(load(SUBSET8), EVAL_CUTOFFS[0])        # MASE scale: rows before the first cutoff, from each client's first reading
# ZZA: Z lets the model choose the error and the trend, A forces an additive season. alias names the output columns.
sf = StatsForecast(models=[AutoETS(model="ZZA", season_length=24, alias="ZZA"), SeasonalNaive(season_length=24)],
                   freq="h", n_jobs=1)
parts, forms, by_client = [], Counter(), defaultdict(list)
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])   # the eight weeks before c, clock hours filled from them
    part = sf.predict(h=HORIZON, level=[95])                          # level=[95] asks for the 95% interval the coverage line scores
    # the first forecast hour must be the cutoff itself, or the window is misaligned
    if part["ds"].min() != c:
        raise ValueError(f"forecast for {c:%Y-%m-%d} does not start at the cutoff")
    parts.append(part)
    for i, uid in enumerate(sf.uids):
        form = sf.fitted_[i, 0].model_["method"]                    # model 0 is the forced AutoETS; its method name is the form
        forms[form] += 1
        by_client[uid].append(form)
forecasts = pd.concat(parts, ignore_index=True)
summary, per_client = score_clients(forecasts, masked, ["ZZA", "SeasonalNaive"], scale, interval_model="ZZA")
show("horizon hours", HORIZON)
show("windows", len(parts))
for form, n in sorted(forms.items()):
    show(f"fits that chose {form}", n)
for label, value in summary.items():
    show(label, value, digits=3 if label.startswith("coverage") else 2)
show("clients where ZZA has lower MASE", int((per_client["ZZA"] < per_client["SeasonalNaive"]).sum()))
show_client_lines(by_client, per_client, ["ZZA", "SeasonalNaive"])
```

Output:

```text
horizon hours: 24
windows: 3
fits that chose ETS(A,Ad,A): 1
fits that chose ETS(A,N,A): 17
fits that chose ETS(M,N,A): 6
clients: 8
scored hours per client: 72
MAE ZZA: 365.24
RMSE ZZA: 553.11
MASE ZZA: 1.17
MAE SeasonalNaive: 423.68
RMSE SeasonalNaive: 591.25
MASE SeasonalNaive: 1.16
coverage 95 ZZA: 0.925
clients where ZZA has lower MASE: 4
forms MT_014, one per cutoff: ETS(A,N,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_014 ZZA: 1.08
MASE MT_014 SeasonalNaive: 0.97
forms MT_064, one per cutoff: ETS(A,N,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_064 ZZA: 1.27
MASE MT_064 SeasonalNaive: 1.08
forms MT_115, one per cutoff: ETS(M,N,A) ETS(M,N,A) ETS(M,N,A)
MASE MT_115 ZZA: 0.95
MASE MT_115 SeasonalNaive: 1.31
forms MT_166, one per cutoff: ETS(A,Ad,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_166 ZZA: 1.18
MASE MT_166 SeasonalNaive: 1.29
forms MT_217, one per cutoff: ETS(M,N,A) ETS(M,N,A) ETS(M,N,A)
MASE MT_217 ZZA: 1.78
MASE MT_217 SeasonalNaive: 1.25
forms MT_268, one per cutoff: ETS(A,N,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_268 ZZA: 0.94
MASE MT_268 SeasonalNaive: 0.89
forms MT_319, one per cutoff: ETS(A,N,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_319 ZZA: 1.11
MASE MT_319 SeasonalNaive: 1.26
forms MT_370, one per cutoff: ETS(A,N,A) ETS(A,N,A) ETS(A,N,A)
MASE MT_370 ZZA: 1.05
MASE MT_370 SeasonalNaive: 1.25
```

On mean MASE, forcing the season brings AutoETS within a hair of seasonal naive, though not below it: 1.17 against 1.30 for the default and 1.16 for seasonal naive.

The forced season helps some clients and hurts others. It lowers the lead client's MASE, from 1.18 to 1.08, and `MT_064`'s too, but it raises `MT_370`'s, from 0.96 to 1.05. So forcing the season is a change to test on each client, not a fix to apply to all of them.

**Working rule:** Start with AutoETS for hourly demand with `season_length=24`, and print the chosen forms in every backtest. When a client takes a flat form, check that its seasonal form is not failing. If the seasonal fit has the lower likelihood, force the season with `model="ZZA"`, and score both forms on earlier windows before you keep either: cutoffs before the held-out week that the report does not score, such as the four ordinary days in late November and early December 2014, which [Chapter 5](#choose-on-decision-windows) sets aside for choices. The standard cutoffs show the comparison here, but they do not decide it. When a forecast gets worse, look first for a form that changed between cutoffs.

## Fit a fixed seasonal ARIMA {#fit-a-fixed-seasonal-arima}

The second candidate models what seasonal naive leaves behind. The backtests of Chapter 3 are the test for what it adds. An ARIMA model writes the next reading as a weighted sum of earlier readings and earlier errors, after differencing: subtracting a reading from the reading one season earlier. The model is written ARIMA(p,d,q)(P,D,Q)[m]. The non-seasonal part has p autoregressive terms, d differences and q moving-average terms. The seasonal part has the same three, at lags that are multiples of the season length m.

The book's model is ARIMA(1,0,0)(1,1,0)[24]. It has one autoregressive term, no ordinary difference, no moving-average term, one seasonal difference at lag 24, and one seasonal autoregressive term at lag 24. Written out, with B the step back operator, so that B y_t is y_(t-1):

`(1 - phi1 B)(1 - Phi1 B^24)(1 - B^24) y_t = e_t`

The term `(1 - B^24)` replaces each reading with its change from the same hour yesterday. The lag of 24 is the point of the model for hourly demand. Each hour is compared with the same hour yesterday, which is the comparison seasonal naive makes, and the autoregressive terms then model what that comparison leaves behind. The seasonal difference removes the level, so the model has no mean term. statsforecast's `ARIMA` leaves the mean off for differenced series by default (`statsforecast/models.py`, the `ARIMA` docstring).

We fix the order rather than search for it, and [the section on automatic search](#why-the-book-avoids-autoarima) explains why. Before the order goes into a backtest, fit it once with statsmodels 0.15.0 on the lead client's history before the first standard cutoff, and print the names of the fitted parameters. That shows whether the model has the terms you wrote down.

Example `arima-summary-look` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsmodels 0.15.0 · utilsforecast 0.2.17), passing in Edition 2026.11.13:

```python
"""Fit the fixed seasonal ARIMA with statsmodels on the lead client's history before the first standard cutoff, and print its parameter names. The parameter lines are what the prose reads."""
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from lib.backtest import history_before
from lib.electricity import load
from lib.settings import EVAL_CUTOFFS, LEAD, show

hist = history_before(load([LEAD]), pd.Timestamp(EVAL_CUTOFFS[0]))
y = pd.Series(hist["y"].to_numpy(), index=pd.DatetimeIndex(hist["ds"], freq="h"))
res = SARIMAX(y, order=(1, 0, 0), seasonal_order=(1, 1, 0, 24)).fit(disp=False)
show("hours of history", len(y))
for name in res.params.index:
    show("parameter", name)
```

Output:

```text
hours of history: 1344
parameter: ar.L1
parameter: ar.S.L24
parameter: sigma2
```

The list has three names: `ar.L1`, `ar.S.L24` and `sigma2`. The first is the autoregressive term, which says how much an hour's change from the same hour yesterday carries into the next hour. The second is the seasonal term at lag 24, which says how much a day's change at an hour carries into the same hour the next day. The third is the variance of the error. The list has no intercept. statsmodels adds one to a seasonal ARIMA only when `trend` is set, so the list would show none whether or not the series is differenced, and the seasonally differenced model needs none in any case. A full statsmodels summary also gives each value. This book does not quote them. The values change with the window and the library version, so a reader needs what each term means more than its number.

The fixed model is then one more candidate in the backtest, beside AutoETS and seasonal naive. Its scores come in the [comparison section](#compare-models-on-the-same-cutoffs) below.

**Working rule:** When a search is too slow to run at every cutoff, fix the order and write it in the call. Print the summary once, and check that the terms it lists are the ones you meant. Refit the fixed order at every cutoff, as you would refit any model. The order stays fixed. The coefficients do not.

## Compare models on the same cutoffs {#compare-models-on-the-same-cutoffs}

Four forecasts now cover the same 24 hours at the same three cutoffs, from the same eight weeks of history, for the same eight clients: seasonal naive, AutoETS, AutoETS with the season forced, and ARIMA. Each backtest is a separate script, so each finishes well inside the 45 seconds the book allows an example on two CPUs.

One score is still missing: the fixed ARIMA's, on the same windows and measures.

Example `arima-subset-backtest` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.13:

```python
"""Backtest the fixed seasonal ARIMA(1,0,0)(1,1,0)[24] and seasonal naive for the eight clients of SUBSET8 over the three standard cutoffs.
The MASE gap and the count of clients where ARIMA wins, printed last, are the figures the comparison section quotes."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import ARIMA, SeasonalNaive

from lib.scoring import book_scale
from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, HORIZON, SEED, SUBSET8, show
from lib.subsets import score_clients

np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
masked = mask_clock_changes(load(SUBSET8))                  # clock-change hours become NaN, so they are never scored; filled_history fills them from their neighbours before each fit
scale = book_scale(load(SUBSET8), EVAL_CUTOFFS[0])        # MASE scale: rows before the first cutoff, from each client's first reading
# The order is fixed, not searched: one AR term, one seasonal difference and one seasonal AR term, all at lag 24.
# n_jobs=1 keeps the output the same from run to run.
sf = StatsForecast(models=[ARIMA(order=(1, 0, 0), season_length=24, seasonal_order=(1, 1, 0)),
                           SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
parts = []
for c in pd.to_datetime(EVAL_CUTOFFS):
    sf.fit(df=filled_history(masked, c)[["unique_id", "ds", "y"]])   # the eight weeks before c, clock hours filled from them
    part = sf.predict(h=HORIZON)
    # the first forecast hour must be the cutoff itself, or the window is misaligned
    if part["ds"].min() != c:
        raise ValueError(f"forecast for {c:%Y-%m-%d} does not start at the cutoff")
    parts.append(part)
forecasts = pd.concat(parts, ignore_index=True)

summary, per_client = score_clients(forecasts, masked, ["ARIMA", "SeasonalNaive"], scale)
show("horizon hours", HORIZON)
show("windows", len(parts))
for label, value in summary.items():
    show(label, value)
show("MASE gap, SeasonalNaive minus ARIMA", summary["MASE SeasonalNaive"] - summary["MASE ARIMA"])
show("clients where ARIMA has lower MASE", int((per_client["ARIMA"] < per_client["SeasonalNaive"]).sum()))
```

Output:

```text
horizon hours: 24
windows: 3
clients: 8
scored hours per client: 72
MAE ARIMA: 386.13
RMSE ARIMA: 576.30
MASE ARIMA: 1.09
MAE SeasonalNaive: 423.68
RMSE SeasonalNaive: 591.25
MASE SeasonalNaive: 1.16
MASE gap, SeasonalNaive minus ARIMA: 0.07
clients where ARIMA has lower MASE: 5
```

MAE is in kilowatt hours, and [RMSE](#score-on-a-held-out-week), the root mean squared error, punishes large misses more. Both are computed for each client over its 72 scored hours, then averaged over the eight clients, so each client counts once. [MASE](#scale-errors-with-mase) divides each client's MAE by the MAE that seasonal naive makes in its own history, over every reading before Dec 29, 2014, from each client's first reading and with the clock-change hours left out, then averages over clients. A MASE of 1 means the model is as accurate as seasonal naive was on its own past. The [coverage](#why-one-number-is-not-enough) of AutoETS is the share of scored hours that fall inside its 95% [prediction interval](#why-one-number-is-not-enough), the range the model gives for each hour.

| Model | MAE (kWh) | RMSE (kWh) | MASE | Clients beating seasonal naive on MASE |
| --- | --- | --- | --- | --- |
| SeasonalNaive | 423.68 | 591.25 | 1.16 | not applicable |
| AutoETS | 362.11 | 537.20 | 1.30 | 4 |
| AutoETS, season forced (ZZA) | 365.24 | 553.11 | 1.17 | 4 |
| ARIMA | 386.13 | 576.30 | 1.09 | 5 |

Read the last column as a count out of the eight clients, not as a score. The AutoETS intervals cover 0.910 of the scored hours, and the forced-season intervals cover 0.925. The nominal share is 0.95, so the intervals are a little narrow on this sample. Coverage checks the intervals, not the point forecast. An interval that covers too little is too narrow, and a planner who buys to it will be short more often than its label says. Chapter 8 returns to intervals and shows how to calibrate them on earlier windows.

The two measures disagree about AutoETS. Its mean MAE is the lowest of the four rows, and its mean MASE is the highest. MAE in kilowatt hours gives more weight to the clients with large loads, because their errors are large. MASE scales each client's error by that client's own history, so every client counts about the same. The per-client lines in the AutoETS run show where the MASE comes from. `MT_064` has a MASE of 2.32, against 1.08 for seasonal naive, and it is one of the flat-form clients. `MT_217` has 1.76, against 1.25, and its form changes from one cutoff to the next. The ranking depends on the measure, so the choice of measure is part of the decision.

Three windows are a small sample, as [Chapter 3](#why-one-test-week-misleads) explains. AutoETS beats seasonal naive on 4 of the eight clients, and ARIMA on 5. ARIMA is better than seasonal naive on both measures, and on MASE by 0.07. Three windows can't settle a gap that small.

**Working rule:** Score every candidate on the same cutoffs, with the same history and the same scale, and report MAE and MASE side by side. When the two disagree, say which one the decision needs. We recommend more windows before choosing between two models that differ by less than about a tenth of MASE. That threshold is a judgement from this sample, not a measurement.

## Meet the late starters {#meet-the-late-starters}

One client in the subset starts late. `MT_115`'s first non-zero reading is at 00:00 on Jan 14, 2014. Before that, the meter reports zeros, and the data flags those hours `before_first_reading`. Those zeros are not low use. A model that reads them learns a level the client does not have. A late starter is a client whose first reading falls inside the history its model reads. The fix is the start rule: a series begins at its first reading. This matters for the supplier's decision. A level pulled low means buying too little for that client, the costlier of the supplier's two errors.

At the December cutoffs the eight weeks before each one are all readings, so this section uses February cutoffs: Feb 1, 2014, Feb 15, 2014 and Feb 28, 2014. Their eight-week histories still reach back before the first reading, so the case is in them. [Chapter 6](#forecast-many-clients-at-once) applies the same rule to all thirty clients.

### A history that starts with zeros {#a-history-that-starts-with-zeros}

Start with the raw history, the eight weeks before each February cutoff with its zeros included. The share of zero hours in that history is 68% on Feb 1, 2014, 43% on Feb 15, 2014 and 20% on Feb 28, 2014. The share falls as the cutoff passes the first reading.

Starting the history at the first reading may fix it. Fitting AutoETS twice at each February cutoff, once on the raw eight weeks and once on the start history, which begins at `MT_115`'s first reading, shows whether it does, scored on the 24 hours from each cutoff.

Example `late-starter-trim` (Python 3.13.16 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.13:

```python
"""Backtest AutoETS for MT_115, a late starter, on three February cutoffs: once on its raw eight weeks and once on its history from its first reading.
The start-rule counts, printed first, and the three-window MAE lines are the figures the point rests on."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

from lib.backtest import history_before
from lib.electricity import load
from lib.quirks import fill_clock_change_hours, mask_clock_changes
from lib.settings import HORIZON, SEED, SUBSET8, show
from lib.starts import check_start_rule, history_from_start

LATE = "MT_115"                                             # the one late starter in SUBSET8, first non-zero reading on Jan 14, 2014
# February cutoffs: at the December cutoffs every hour of the history is a reading, so the rule changes nothing there
CUTOFFS = pd.to_datetime(["2014-02-01", "2014-02-15", "2014-02-28"])

np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
dropped, flagged = check_start_rule(load(SUBSET8))           # raises unless the rule drops exactly the flagged rows, so the counts agree
show("start rule drops, SUBSET8", dropped)
show("flagged before_first_reading, SUBSET8", flagged)
masked = mask_clock_changes(load([LATE]))[["unique_id", "ds", "y", "quirk"]]


def fit_and_score(hist, c):
    """Fit AutoETS on one history, forecast the 24 hours from c, and score it on those hours."""
    sf = StatsForecast(models=[AutoETS(season_length=24)], freq="h", n_jobs=1)
    sf.fit(df=fill_clock_change_hours(hist)[["unique_id", "ds", "y"]])   # clock-change hours filled from their neighbouring hours, as elsewhere
    fc = sf.predict(h=HORIZON)
    actual = masked[(masked["ds"] >= c) & (masked["ds"] < c + pd.Timedelta(hours=HORIZON))]   # the day's 24 readings, to score against
    joined = fc.merge(actual[["ds", "y"]], on="ds", how="left")
    # the form's method name, the mean forecast, the day's MAE, and the mean of the readings
    return sf.fitted_[0, 0].model_["method"], float(joined["AutoETS"].mean()), float((joined["y"] - joined["AutoETS"]).abs().mean()), float(joined["y"].mean())


maes = {"raw": [], "start": []}
for c in CUTOFFS:
    raw_hist = history_before(masked, c)                     # the eight weeks before c, zeros included; it insists on exactly 1,344 rows
    # the share of hours that read zero, including the leading zeros before the first reading
    show(f"zero percent before {c:%Y-%m-%d}", round(100 * (raw_hist["y"] == 0).mean()))
    # the start history begins at the first reading, so it is shorter wherever the client starts late
    for label, hist in [("raw", raw_hist), ("start", history_from_start(masked, c))]:
        form, fc_mean, window_mae, actual_mean = fit_and_score(hist, c)
        show(f"{label} history hours {c:%Y-%m-%d}", len(hist))
        show(f"{label} form {c:%Y-%m-%d}", form)
        show(f"{label} mean forecast {c:%Y-%m-%d}", fc_mean)
        show(f"{label} mean actual {c:%Y-%m-%d}", actual_mean)
        show(f"MAE {label} {c:%Y-%m-%d}", window_mae)
        maes[label].append(window_mae)
for label in maes:
    show(f"MAE {label}, three windows", np.mean(maes[label]))
    show(f"MAE {label}, 2014-02-15 and 2014-02-28", np.mean(maes[label][1:]))   # [1:] skips Feb 1, the first cutoff
```

Output:

```text
start rule drops, SUBSET8: 9072
flagged before_first_reading, SUBSET8: 9072
zero percent before 2014-02-01: 68
raw history hours 2014-02-01: 1344
raw form 2014-02-01: ETS(A,N,N)
raw mean forecast 2014-02-01: 16.43
raw mean actual 2014-02-01: 24.06
MAE raw 2014-02-01: 8.81
start history hours 2014-02-01: 432
start form 2014-02-01: ETS(M,Ad,A)
start mean forecast 2014-02-01: 23.88
start mean actual 2014-02-01: 24.06
MAE start 2014-02-01: 3.72
zero percent before 2014-02-15: 43
raw history hours 2014-02-15: 1344
raw form 2014-02-15: ETS(A,N,A)
raw mean forecast 2014-02-15: 24.54
raw mean actual 2014-02-15: 27.11
MAE raw 2014-02-15: 4.29
start history hours 2014-02-15: 768
start form 2014-02-15: ETS(M,Ad,A)
start mean forecast 2014-02-15: 23.84
start mean actual 2014-02-15: 27.11
MAE start 2014-02-15: 4.77
zero percent before 2014-02-28: 20
raw history hours 2014-02-28: 1344
raw form 2014-02-28: ETS(A,N,A)
raw mean forecast 2014-02-28: 23.73
raw mean actual 2014-02-28: 23.54
MAE raw 2014-02-28: 2.93
start history hours 2014-02-28: 1080
start form 2014-02-28: ETS(M,Ad,A)
start mean forecast 2014-02-28: 22.48
start mean actual 2014-02-28: 23.54
MAE start 2014-02-28: 2.73
MAE raw, three windows: 5.34
MAE raw, 2014-02-15 and 2014-02-28: 3.61
MAE start, three windows: 3.74
MAE start, 2014-02-15 and 2014-02-28: 3.75
```

The damage is in the level, and it is worst on Feb 1. AutoETS fits the raw history without an error and forecasts without a warning. On Feb 1, 2014 it chooses the flat form, ETS(A,N,N), and its forecast averages 16.43 kWh an hour over the day. The readings that followed average 24.06 kWh. The MAE on that day is 8.81 kWh. The likely cause is the zeros: they pull the level down, and the model cannot tell that they are not use.

On the other two days the raw history's errors are much smaller, at 4.29 kWh on Feb 15, 2014 and 2.93 kWh on Feb 28, 2014. So the damage depends on how many zeros the window holds. The rule is right whatever the zero share, because leading zeros are not use.

### Start each series at its first reading {#start-each-series-at-its-first-reading}

The start rule says that a series begins at its first reading. It drops every reading before the client's first non-zero reading, and it keeps every reading after that, zeros included, because the zeros after the start are real low use and a model needs them. A window that begins after the first reading keeps all its hours, since the rule removes leading zeros only. The rule lives in `examples/lib/starts.py`, so later chapters call the same code. Its function `history_from_start(df, cutoff)` returns one cutoff's history under the rule: the readings in the eight weeks before the cutoff, from the first reading onward. It finds that first reading from the rows before the cutoff only, so no reading after the cutoff reaches the model. It raises an error if a client has no reading before the cutoff, or fewer than 48 hours of history.

Before the rule is used, check that it does what the flag says. `check_start_rule` counts the rows the rule would drop across the whole series, and raises an error unless those rows are exactly the rows flagged `before_first_reading`. On the subset, the rule drops 9072 hours, and the flag marks 9072. They match. The only late starter in the subset is `MT_115`.

The rule shortens the history most at the first cutoff, 432 hours against 1,344, and less as the cutoff moves past the first reading: 768 hours on Feb 15 and 1080 on Feb 28.

The start history picks ETS(M,Ad,A) at all three cutoffs, a form with multiplicative error, damped trend and additive season. The raw history changes its form between days, from the flat form on Feb 1 to ETS(A,N,A) on Feb 15, 2014 and ETS(A,N,A) on Feb 28, 2014.

The three-window MAE falls from 5.34 kWh to 3.74 kWh. The gain is uneven across the windows, and all of that gain comes from Feb 1, where the MAE falls from 8.81 to 3.72 kWh.

On Feb 15 the rule does worse, and on Feb 28 it does a little better. Over those two days together the raw history does slightly better, with a mean MAE of 3.61 kWh against 3.75.

The fits show how the rule loses on Feb 15. The start history is still short, 768 hours, and its damped trend forecasts lower than the raw fit does: 23.84 kWh an hour on average, against 24.54 for the raw fit, when the readings averaged 27.11 kWh. That low forecast is the cost the case warns about. One client and three days are a small sample, so the figures illustrate the rule rather than prove it.

**Working rule:** When a client's history holds zeros, check whether its first non-zero reading falls inside the history. If it does, apply the start rule before any model sees the history, whatever the zero share, because leading zeros are not use. Run `check_start_rule` on the whole series first, and if it fails, find out why before you trim anything. Print the history length at each cutoff, because a short history is the first sign that the rule has taken too much.

## Why the book avoids automatic ARIMA at season 24 {#why-the-book-avoids-autoarima}

AutoARIMA searches for the orders instead of fixing them. It runs a stepwise search over candidate orders, picks the best by AICc, which is its default, and stops after at most 94 candidate models (statsforecast 2.1.1, `statsforecast/models.py`, and the stop message in `statsforecast/arima.py`). Each candidate is a full state-space fit. With a season of 24, each candidate that has seasonal terms at lag 24 is slow, and the search tries dozens of them, so it takes far longer than the fits in this chapter.

On the book's pinned setup, two CPUs with statsforecast 2.1.1, one window for one client took about 75 seconds. That was one run on `MT_014` at the first standard cutoff. The subset needs 24 such windows, so one backtest of it would take about half an hour, against the 45 seconds the book allows an example. That is this book's own measurement, not an example in it, and it depends on the setup, so time it on your own machine before you plan a schedule around it. The fixed order costs one fit per window, which is the difference that matters here. Its weak point is a client whose pattern differs from the order's assumptions. The backtest is the check for that, and the [scores in the comparison section](#compare-models-on-the-same-cutoffs) are the place to look.

A fixed order is a judgement, not a finding. We chose (1,0,0)(1,1,0) with a season of 24 because the data has a daily pattern and the backtests in this chapter need a model that finishes. The order sits in the call, where a reader can see it and change it. Later chapters compare against it on the same windows, so a change to the order shows up in the scores.

**Working rule:** Do not run an automatic search with a season of 24 on hourly data in a schedule that refits every day. Time the search on one client before you commit to it. If it is too slow, fix the order and test that order in the backtest.

## What goes wrong in production {#what-goes-wrong-ch4}

- **A missing season.** A season length left at 1 gives a model with no daily pattern, and no error. The sign is that every client chooses a form with no season, such as ETS(A,N,N). A few clients doing so is a different case: a seasonal fit that fails, which the flat-form check in [the exponential smoothing section](#fit-exponential-smoothing) tests. Log the chosen forms at each refit.
- **A late starter's zeros.** A client that begins inside the history has its level pulled down until its first reading leaves the window. The sign is a forecast that runs low for days after the start. Count the zero share of each client's history before each refit, and apply the start rule to any client whose first reading falls inside the history.
- **Forms that change.** The chosen form can change between refits for one client. That is not wrong in itself, but a switch from a seasonal form to one with no season is worth checking against the readings. Keep the forms in the run log.
- **Costs that add up.** Fits scale with clients, times windows, times refits. Count them before you add clients to a schedule.
- **Intervals that miss.** The AutoETS intervals covered 0.910 of hours on this sample, short of the nominal 0.95. Chapter 8 shows how to calibrate bands on earlier windows, and until a band is calibrated that way, do not present it as a 95% range.
- **How you would notice.** Run seasonal naive beside every statistical model on each day's windows, and log the MASE gap. A gap that changes sign from day to day is the signal to look at the model, not a result to report.

## Decisions this chapter made {#decisions-ch4}

- **AutoETS with a season of 24.** The default `model="ZZZ"` and the forced-season run, `model="ZZA"`, are both reported, because a flat choice can be a failed seasonal fit. This chapter makes no choice between the two forms: the standard-cutoff comparison is reported, not used to choose, and the choice belongs on earlier windows. [Chapter 1](#forecast-with-a-statistical-model) forced `ZZA` on the lead client, and this chapter shows the forced run for all eight.
- **A fixed ARIMA(1,0,0)(1,1,0)[24], with no search.** This is a stated judgement, and the backtest is what tests it.
- **Eight clients, not thirty.** Chapter 6 fits all thirty clients with one model. A per-client fit of AutoETS for all thirty over three windows takes about 97 seconds on the pinned setup, against the 45 seconds the book allows an example, so this chapter uses the subset.
- **The subset, the cutoffs and the scale.** `SUBSET8`, the three standard cutoffs, Dec 29 to Dec 31, 2014, 1,344 hours of history, and seasonal naive as the bar in every comparison. The MASE scale reads each client from its first reading, with the clock-change hours left out.
- **The clock-change hours.** Every subset example masks them and fills them from history, as [Chapter 3](#mark-clock-change-hours-as-missing) sets out. None of the three windows holds a clock-change hour, so the masking changes no forecast and no scored hour. It does change the MASE scale, because the scale reads all history before Dec 29, 2014, and it counts `MT_115` from Jan 14, 2014.
- **Late starters: February cutoffs and the start rule.** The December cutoffs do not meet `MT_115`'s late start, so the February cutoffs do. Chapter 6 applies the rule to all thirty clients.
- **Coverage for the two AutoETS runs only.** The ARIMA backtest is scored without intervals here.
- **No fitted values quoted.** The ARIMA script prints parameter names only, and the flat-form check prints counts only. Errors are rounded to two decimals and coverage to three.
- **A statistical baseline for Chapter 5.** The per-client AutoETS and ARIMA scores on these windows are the bar the gradient boosting model must beat.
- **What to carry forward.** A flat form can be a failed seasonal fit, so read the chosen forms beside every score. MAE and MASE can rank models differently, so say which one the decision needs. Start each series at its first reading, and add windows before choosing between close models.
