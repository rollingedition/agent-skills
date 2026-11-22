---
title: "Time Series Forecasting"
chapter: "Quantify forecast uncertainty"
chapter_id: quantify-forecast-uncertainty
book: time-series-forecasting
edition: 2026.11.14
verified: 2026-11-22
edition_code: 63J0-VQVZ
canonical: https://rollingedition.com/time-series-forecasting/quantify-forecast-uncertainty
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Quantify forecast uncertainty,” chapter 8 of Time Series Forecasting, Edition 2026.11.14, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/quantify-forecast-uncertainty. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Quantify forecast uncertainty

This chapter puts a range around each day-ahead forecast, so you can say whether a purchase can rely on it. You'll calibrate prediction intervals on days that come before the days you score, measure how often they hold, and choose the level to buy at from the two costs of an error.

## Why one number is not enough {#why-one-number-is-not-enough}

The forecasts so far give one number for each client and hour, and a single number is not enough to buy on. The supplier cannot buy an expected value. It buys an amount of power a day ahead for each hour, so it needs a range around each forecast. Each kWh it buys is either used or not. Buying short means buying the rest later at a premium, and buying long means paying for power that nobody uses. The two errors cost different amounts, so the right purchase is usually not the forecast itself. Take one hour. Suppose the forecast is 100 kWh. If the reading turns out 10 kWh higher, the supplier is short and pays the short cost on those 10 kWh. If it turns out 10 kWh lower, the supplier has 10 kWh it pays for and does not use. When the short cost is three times the unused cost, a purchase above the forecast costs less on average, because it makes the expensive error less likely. How far above the forecast the purchase should sit depends on that ratio, and on how wide the errors are.

This chapter states two costs as assumptions. A kWh bought short costs 3.00 cost units, and a kWh bought and not used costs 1.00. These numbers are illustrative. They are not prices, and the book does not claim that any real supplier faces them. [A later section](#choose-the-level-from-the-cost-of-error) shows how they set the purchase.

A prediction interval gives a lower and an upper bound for each hour. A prediction interval's level, such as 80 or 95, is the share of readings the bounds should contain. The share of readings the bounds contain is the coverage, and coverage belongs to many forecasts made the same way, not to one. One day's band either contains the readings or it does not. Across the 72 hours of three days, the share inside the band is a measurement. Across a year of days, it becomes a track record. A 95 percent band whose hours fall inside it 90 percent of the time has undercovered, but no single day shows it. Only the average over many hours shows it, and that average is what we measure.

Quantiles connect the bands to the costs. The lower bound of a central 80 percent interval is the 0.1 quantile of the forecast's distribution, the value that the reading falls below one time in ten. The upper bound is the 0.9 quantile. The purchase that minimises the expected cost is also a quantile, and [Choose the level from the cost of error](#choose-the-level-from-the-cost-of-error) derives which one.

In the case, the range that matters is the total's, because the total is what the supplier buys. [Chapter 6](#one-model-for-many-clients) forecast the thirty clients with one global model, and the total is the hourly sum of those forecasts. Each client has its own range, but the total's range cannot be read off the clients' ranges by adding them. [Choose the level from the cost of error](#choose-the-level-from-the-cost-of-error) compares the two.

**Working rule:** Ask for a range wherever the costs of the two errors differ, and choose its level from those costs rather than from a number that looks reassuring. Report coverage as the share of hours inside the band over many windows, never as the chance that one day falls inside.

## Build intervals from residuals {#build-intervals-from-residuals}

A range needs bounds, and the simplest bounds come from past errors. A residual is the error of an earlier forecast: the reading minus the forecast, `e = y - f`. Conformal prediction builds a band from the residuals of forecasts made the same way on earlier days. Take the residuals of a set of calibration windows, group them by horizon step, and read off the quantiles you need. A day-ahead forecast made at 00:00 has one horizon step for each hour of the day, so the group is the hour alone. For a level `L` in percent, the bounds for a forecast `f` made at a given step are:

```text
lower = f + Q((1 - L/100) / 2)
upper = f + Q((1 + L/100) / 2)
```

where `Q(p)` is the empirical p-quantile of the calibration residuals at that step. The method assumes no model of the errors. It only assumes that the calibration residuals resemble the residuals to come, which [a later section](#calibrate-on-earlier-windows) tests. A calibration window is a cutoff whose residuals size the bands. It always comes before the cutoffs being forecast, and it is never one of the windows that are scored.

The library that does this for the book's model is mlforecast, at version 1.1.0. Its class `PredictionIntervals` takes a number of windows, a horizon and a method, and it has four conformal methods: `conformal_error`, `conformal_distribution`, and their weighted versions. The two unweighted methods score the absolute residuals, `|y - f|`, so their bounds are symmetric around the forecast (mlforecast 1.1.0, `mlforecast/conformal_prediction.py`, function `compute_conformity_scores`). The default, `conformal_distribution`, works one client and one horizon step at a time. For each client and step it takes the calibration windows' absolute residuals, makes the paths of the forecast plus and minus each one, and reads the quantiles of those paths. Nothing is pooled across clients. The statistical library, statsforecast at version 2.1.1, names its interval class `ConformalIntervals`, not `PredictionIntervals`.

To see what the library does with a short calibration history, run its class with three calibration windows. It scores the three standard cutoffs, Dec 29 to Dec 31, 2014, each at 00:00. Those are the held-out week's last three days, and the days this chapter scores. mlforecast refits the global model at each cutoff and calibrates each one on the three before it.

Example `conformal-three-windows` (Python 3.13.16 · holidays 0.110.dev20261119030846 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.14:

```python
"""mlforecast's own conformal intervals, with three calibration windows, refitted at each of the three standard cutoffs.
Compare the coverage at 80 and 95 with their labels, and with the highest coverage three windows allow."""
import pandas as pd

from lib.electricity import load
from lib.intervals import builtin_intervals, design_coverage, symmetric_ceiling
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
# Every clock-change hour (four changes, 2013 and 2014) is masked as NaN. builtin_intervals keeps only rows from Oct 27, 2014 on, so no masked hour is in a window.
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
# One row per client and hour. The bounds are columns named by model and level, such as LGBMRegressor-lo-80.
cv = builtin_intervals(df, pd.to_datetime(EVAL_CUTOFFS))

show("scored hours", len(cv))
show("calibration windows per cutoff", 3)
show("residuals per client and hour", 3)
# Ceiling of a band of plus and minus n absolute residuals, n / (n + 1), with n = 3: at most 3 of the 4 places a new one can take.
show("highest coverage three windows allow, any level", symmetric_ceiling(3), 3)
for level in (80, 95):
    # Simulated under exchangeable normal errors, with mlforecast's construction, to set against the measured coverage.
    show(f"simulated coverage at {level}, exchangeable errors", design_coverage(level, 3, "builtin"), 3)
for level in (80, 95):
    lo, hi = cv[f"LGBMRegressor-lo-{level}"], cv[f"LGBMRegressor-hi-{level}"]
    inside = (cv["y"] >= lo) & (cv["y"] <= hi)
    show(f"coverage at {level}", inside.mean(), 3)
    show(f"mean width at {level}", (hi - lo).mean())
    if level == 80:
        # The by-day lines are printed for the 80 level only. Each hour is grouped by its calendar day.
        day = cv["ds"].dt.floor("D")
        for d, share in inside.groupby(day).mean().items():
            show(f"coverage at 80 on {d:%Y-%m-%d}", share, 3)
        for d, err in (cv["y"] - cv["LGBMRegressor"]).abs().groupby(day).mean().items():
            show(f"mean absolute error on {d:%Y-%m-%d}", err)
```

Output:

```text
scored hours: 2160
calibration windows per cutoff: 3
residuals per client and hour: 3
highest coverage three windows allow, any level: 0.750
simulated coverage at 80, exchangeable errors: 0.656
simulated coverage at 95, exchangeable errors: 0.732
coverage at 80: 0.690
mean width at 80: 281.07
coverage at 80 on 2014-12-29: 0.756
coverage at 80 on 2014-12-30: 0.676
coverage at 80 on 2014-12-31: 0.637
mean absolute error on 2014-12-29: 114.62
mean absolute error on 2014-12-30: 94.42
mean absolute error on 2014-12-31: 163.37
coverage at 95: 0.750
mean width at 95: 355.39
```

The output shows the failure before any fix: across the 2160 client-hours, the bands at the 80 level cover 0.690 and at the 95 level 0.750. Both fall short of their labels, and the bands at 80 are 281.07 kWh wide on average.

The design sets a ceiling, and the 95 result sits on it. With three windows, each client and hour has three absolute residuals, and the band reaches no further than the largest of them. For exchangeable errors, the test error is the largest of four absolute errors one time in four, so the band misses it that often. The highest coverage three windows allow is 0.750, at any level. Under the same exchangeable assumption, the band's expected coverage is 0.656 at 80 and 0.732 at 95. The simulation draws normal errors, with the same construction. The measured figures are a little above those expected values, so the calibration windows did not have smaller errors than the scored days. Calm calibration windows would push coverage below the expected value, not above it. The shortfall is the construction's.

The coverage by day shows where the shortfall sits. At the 80 level it is 0.756 on Dec 29, 0.676 on Dec 30 and 0.637 on Dec 31. The forecast errors on those days were 114.62, 94.42 and 163.37 kWh on average. Dec 31 has the largest errors and the lowest coverage, and three days cannot separate day-to-day variation from the design.

A second problem comes from the calibration. Each cutoff calibrates only on days before it: the bands for Dec 31 use Dec 28, 29 and 30. But Dec 29 and Dec 30 are scored days too. So the three scored windows are not independent, because one window's calibration contains the readings of another scored window. No band uses its own day's readings, and the rule is right for operation, where those readings are known. For a test it weakens the result. Fixing it would need a separate calibration fit for each cutoff, which is more than a one-argument change, so the chapter's own bands use a fixed calibration set instead, as [Calibrate on earlier windows](#calibrate-on-earlier-windows) shows.

**Working rule:** Build each band from the residuals of windows that come before its cutoff, and check the coverage it reaches on windows it did not use before you trust it. Read the level a design can reach before you read the coverage. Three residuals per client and hour cannot reach either label, so the fix is a larger calibration set, not a different reading of the output.

## Calibrate on earlier windows {#calibrate-on-earlier-windows}

The calibration windows must come before the windows you score, and they must not share a target hour with them. The book adds one more rule: a calibration window must not fall on a Portuguese public holiday, because a holiday's load follows the calendar rather than the week before it. The rule applies to the decision windows as well. The held-out evaluation calibrates on twelve ordinary days, Dec 9 to 20, 2014, which end four days before the held-out week. Both examples in this section print the holiday hours and the shared hours in their calibration, and both counts are zero.

Twelve windows with thirty clients give 360 residuals for each hour of the day. They come from twelve days, though, and the thirty clients share each day's weather and calendar. So a day-level error is still a sample of twelve. The pooled residuals have a second problem. The clients differ enormously in size. In the scored week the largest client, MT_370, averages 17499.81 kWh an hour over the three scored days. Pooled residuals in kWh are dominated by such clients, so the bands fit the large clients and misfit the small ones. The fix is to divide each client's residuals by that client's scale before pooling, and multiply the bound back by the scale of the client being forecast. The scale is the seasonal naive error on the history before the first calibration cutoff, the same kind of scale the book uses for MASE. With the scale, the thirty clients count alike.

Two choices in this design were made on the decision windows, not on the held-out evaluation. The [decision windows](#choose-on-decision-windows) are the four cutoffs from Nov 25 to Dec 3, 2014. Their calibration is Nov 9 to 20, 2014, twelve holiday-free days that end four days before the first decision cutoff, the same shape as the held-out design. The windows are scored on their own, and the held-out evaluation is not read. The choices are judged by the interval score and the lowest client's coverage. The interval score adds a band's width to a penalty for each reading that misses the band, the penalty growing with the distance of the miss and scaled by 2 over the miss rate ([Gneiting and Raftery (2007)](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf), eq. 43). Those windows settle both choices, as the measurements below show.

Example `conformal-decision-windows` (Python 3.13.16 · holidays 0.110.dev20261119030846 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.14:

```python
"""The two calibration choices, scaling each client's residuals and the finite-sample levels, decided on the four decision
windows (Nov 25 to Dec 3, 2014), with calibration on Nov 9 to 20. Compare the lowest client's coverage and the interval scores printed for each variant;
the standard cutoffs are not read."""
from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.intervals import DECISION_CAL, bounds, calibration_facts, coverage, interval_score, paired, total_of
from lib.panel import ALL30, DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.scoring import book_scale
from lib.settings import show

raw = load(ALL30)
# Every clock-change hour (four changes, 2013 and 2014) is masked as NaN, as in every example of this chapter.
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
# One row per client and hour, with the forecast f, the reading y and the residual e.
cal, sc = paired(df, DECISION_CAL), paired(df, DECISION_CUTOFFS)
# Each client's MASE-style scale, from the history before the first calibration cutoff.
scale = seasonal_scale(book_scale(raw, DECISION_CAL[0]))

for label, value in calibration_facts(df, DECISION_CUTOFFS, DECISION_CAL).items():
    show(label, value)
show("residuals per hour of the day", len(cal) // 24)
variants = (("unscaled", None, False), ("scaled", scale, False),
            ("unscaled, finite", None, True), ("scaled, finite", scale, True))
for name, s, fin in variants:
    for level in (80, 95):
        # scale=None pools the raw kWh residuals; finite=True applies the (n + 1) quantile correction.
        lo, hi = bounds(sc, cal, level, scale=s, finite=fin)
        show(f"{name}, coverage at {level}", coverage(sc["y"], lo, hi), 3)
        show(f"{name}, interval score at {level}", interval_score(sc["y"], lo, hi, level))
    lo, hi = bounds(sc, cal, 80, scale=s, finite=fin)
    # Coverage per client, then the lowest of the thirty clients.
    show(f"{name}, lowest client coverage at 80", ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean().min(), 3)
# One series, so no scale: the scale exists only to pool clients of different size.
tcal, tsc = total_of(cal), total_of(sc)
for name, fin in (("total", False), ("total, finite", True)):
    lo, hi = bounds(tsc, tcal, 80, finite=fin)
    show(f"{name}, coverage at 80", coverage(tsc["y"], lo, hi), 3)
    show(f"{name}, interval score at 80", interval_score(tsc["y"], lo, hi, 80))
```

Output:

```text
calibration windows: 12
holiday hours in calibration: 0
calibration hours shared with scored: 0
residuals per hour of the day: 360
unscaled, coverage at 80: 0.809
unscaled, interval score at 80: 603.88
unscaled, coverage at 95: 0.957
unscaled, interval score at 95: 1950.32
unscaled, lowest client coverage at 80: 0.021
scaled, coverage at 80: 0.834
scaled, interval score at 80: 336.72
scaled, coverage at 95: 0.954
scaled, interval score at 95: 581.28
scaled, lowest client coverage at 80: 0.365
unscaled, finite, coverage at 80: 0.811
unscaled, finite, interval score at 80: 604.19
unscaled, finite, coverage at 95: 0.959
unscaled, finite, interval score at 95: 1961.48
unscaled, finite, lowest client coverage at 80: 0.021
scaled, finite, coverage at 80: 0.835
scaled, finite, interval score at 80: 337.31
scaled, finite, coverage at 95: 0.956
scaled, finite, interval score at 95: 592.35
scaled, finite, lowest client coverage at 80: 0.375
total, coverage at 80: 0.948
total, interval score at 80: 9268.36
total, finite, coverage at 80: 0.990
total, finite, interval score at 80: 10724.99
```

Scaling wins on the two measures the variants were judged by, and loses only on the pooled coverage at 80. The worst-covered client's coverage at 80 rises from 0.021 to 0.365, and the interval score at 80 falls from 603.88 to 336.72. It falls at 95 as well, as the output shows.

We judged the variants by these two measures because the pooled figure hides clients. We chose them after seeing the decision numbers, so the pooled figure is reported beside them. At 80 the pooled coverage is closer to its label without the scale, at 0.809 against 0.834. The scale stays.

The finite-sample levels stay out of the bands. Each new residual is one more among n + 1, so the finite-sample levels move outward a little: each quantile level moves to `floor((n + 1) * a) / n` for the lower bound and `ceil((n + 1) * (1 - a)) / n` for the upper, where `n` is the number of residuals and `a` the tail share. Their effect on the scaled coverage at 80 is small, from 0.834 to 0.835, and the interval score at 80 gets worse, from 336.72 to 337.31. It gets worse at 95 too, as the output shows. The correction widens the bands and does not help, so the bands do not use it.

The held-out evaluation applies the same design to the standard cutoffs, which are the days the rest of the chapter scores.

Example `conformal-earlier-windows` (Python 3.13.16 · holidays 0.110.dev20261119030846 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.14:

```python
"""Conformal bands for every client, calibrated on twelve holiday-free days before the scored week, with each client's
residuals scaled first. Read the coverage and interval score at 80 and 95 first; the unscaled, three-day and
finite-sample lines are printed for comparison."""
import pandas as pd

from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.intervals import CAL_CUTOFFS, bounds, calibration_facts, coverage, interval_score, paired
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import book_scale
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
scored_cutoffs = pd.to_datetime(EVAL_CUTOFFS)
cal, sc = paired(df, CAL_CUTOFFS), paired(df, scored_cutoffs)
# The scale is read from the history before the first calibration cutoff, as the book's MASE scale is.
scale = seasonal_scale(book_scale(raw, CAL_CUTOFFS[0]))
# The largest client is the one with the highest mean reading over the scored windows.
big = sc.groupby("unique_id")["y"].mean().idxmax()

for label, value in calibration_facts(df, scored_cutoffs).items():
    show(label, value)
show("calibration residuals per hour of the day", len(cal) // 24)
show("largest client", big)
show("mean hourly load of the largest client", sc.groupby("unique_id")["y"].mean().max())
for level in (80, 95):
    lo, hi = bounds(sc, cal, level, scale=scale)
    show(f"coverage at {level}", coverage(sc["y"], lo, hi), 3)
    show(f"mean width at {level}", (hi - lo).mean())
    show(f"interval score at {level}", interval_score(sc["y"], lo, hi, level))
lo, hi = bounds(sc, cal, 80, scale=scale)
per_client = ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean()
show("lowest client coverage at 80", per_client.min(), 3)
# No scale here: the pooled residuals stay in kWh, which is what lets the large clients set the bands.
lo, hi = bounds(sc, cal, 80)
unscaled = ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean()
show("largest client coverage at 80, unscaled residuals", unscaled[big], 3)
# The three calibration days nearest the scored week: Dec 18, 19 and 20, 2014.
recent = cal[cal["cutoff"] >= "2014-12-18"]
lo, hi = bounds(sc, recent, 80, scale=scale)
show("coverage at 80 from three calibration days", coverage(sc["y"], lo, hi), 3)
lo, hi = bounds(sc, cal, 80, scale=scale, finite=True)
show("coverage at 80 with finite-sample levels", coverage(sc["y"], lo, hi), 3)
```

Output:

```text
calibration windows: 12
holiday hours in calibration: 0
calibration hours shared with scored: 0
calibration residuals per hour of the day: 360
largest client: MT_370
mean hourly load of the largest client: 17499.81
coverage at 80: 0.739
mean width at 80: 267.62
interval score at 80: 673.89
coverage at 95: 0.902
mean width at 95: 532.00
interval score at 95: 1326.80
lowest client coverage at 80: 0.472
largest client coverage at 80, unscaled residuals: 0.000
coverage at 80 from three calibration days: 0.711
coverage at 80 with finite-sample levels: 0.741
```

The scaled bands still fall short of both labels on the standard cutoffs: they cover 0.739 of client-hours at 80 and 0.902 at 95. Their mean widths are 267.62 kWh and 532.00 kWh.

The scores are 673.89 at 80 and 1326.80 at 95. They are in kWh, so the large clients dominate them. Lower is better, and the score rewards a band that is both narrow and right.

The pooled bands still have to be read per client. The lowest client coverage at 80 is 0.472, for the client the scaled bands fit least well. With unscaled residuals, the largest client is covered in 0.000 of its hours at 80. The pooled kWh bands were set by the large clients, and they miss the largest client entirely.

Two more checks on the standard cutoffs test the design. Calibrating on only the three days nearest the scored week, Dec 18 to 20, gives 0.711 at 80, against 0.739 with all twelve. Three days are a smaller sample, and the coverage is a little lower. The finite-sample levels give 0.741 at 80, a small change that agrees with the decision windows: the correction does little for the client bands.

**Working rule:** Calibrate on windows that come before the scored ones, with no holiday in them, and scale each client before pooling its residuals. Make each design choice on windows that are not the ones you report. Report how many windows and residuals went into the bands and the coverage they gave on the scored days, even when that coverage falls short of the level.

## Measure coverage on held-out days {#measure-coverage-on-held-out-days}

Coverage is measured on days that the calibration never used. The standard cutoffs give three days, and each day gives 24 hours for each client, so the 2160 client-hours are not that many independent observations. The thirty clients share the calendar and the weather, so the hours of one day agree with one another. For day-level errors the sample is three days, which cannot measure a coverage level. Three days can show that a band fell short on those days, but they cannot say by how much a band falls short over a longer period.

The supplier buys the total, so the total's coverage matters most. Its bands are built from its own residuals over the same twelve days, with the quantiles read directly, and are offered at 80 only, because twelve residuals cannot support 95. With signed bounds, the band from the smallest residual to the largest covers at most 0.846 of the time, if the residuals are exchangeable, and a 95 band, or a 90 band, asks for more.

The total's bands cover 0.667 of its 72 scored hours at 80. For exchangeable errors, the same construction covers 0.682, so most of the gap to 80 comes from the twelve-residual sample. [The section on cost](#choose-the-level-from-the-cost-of-error) puts these bands to use.

The total's errors vary by day. The mean absolute error of the total was 2415.51 kWh on the calibration windows and 2985.88 kWh on the scored days. Dec 31 accounts for most of the gap between the scored days and the calibration windows.

| Scored day | Error of the total, kWh | Coverage at 80 |
| --- | --- | --- |
| Dec 29, 2014 | 2448.53 | 0.625 |
| Dec 30, 2014 | 2149.78 | 0.708 |
| Dec 31, 2014 | 4359.32 | 0.667 |

The coverage does not follow the errors. Dec 29 has the lowest coverage with a middle-sized error, and Dec 31 has the largest error with a middle-sized coverage. Each day has 24 hours, and three days are too few to tell the two apart.

The finite-sample levels would change the total's figure. On the scored days they give 0.736 at 80. The choice was made on the decision windows, where the correction widened the total's bands and worsened their interval score, so the bands do not use it. The decision windows also show that the direction of the gap is not fixed. There the total's 80 bands covered 0.948 of hours, more than their label, and the finite levels pushed that to 0.990.

[Angelopoulos and Bates (2022)](https://arxiv.org/pdf/2107.07511) show that split conformal prediction covers the test point with probability at least `1 - alpha` when the calibration and test points are independent and identically distributed, or more generally exchangeable. They also note that adjacent points in a time series are not exchangeable, using a temperature series as the example. The same holds for hourly load: each hour carries the one before it, and a day's hours share the weather and the calendar. [Barber and co-authors (2023)](https://arxiv.org/abs/2202.13415) call the loss in coverage when exchangeability fails a coverage gap. Their bound does not assume a particular joint distribution. It is small when recent calibration points are weighted in a way that matches the test point's distribution, as in slow drift. That result is theoretical, and this chapter does not test it. A 2026 preprint, [a survey of conformal methods for dependent series](https://arxiv.org/abs/2601.18509), states that temporal dependence violates the exchangeability assumption. It is not peer reviewed, and we cite it only for that point.

Dependence also decides when the misses fall, which a coverage figure cannot show. A band can cover close to its label on average and still miss in long stretches. A 2026 preprint on gridded temperature forecasts, [Distribution-Free Uncertainty Quantification for Weather Forecasting](https://arxiv.org/abs/2611.24329) (arXiv:2611.24329v1, read Nov 21, 2026), measures this. Its author reports that conformal bands fitted cell by cell reach near their nominal coverage of 2 m temperature from the ERA5 reanalysis. Yet the share of cells covered varies from day to day about 3 to 10 times as much as independent cells would give, and the misses cluster in time, both for a small CNN and for the ECMWF HRES forecast. It is one preprint, on one variable and one coarse grid, so we take only the caution from it and test it on the total's bands at 80.

Example `total-band-miss-runs` (Python 3.13.16 · holidays 0.110.dev20261119030846 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.14:

```python
"""Whether the total's misses at 80 come in runs: the longest run of missed hours and the share of misses whose next
hour also misses, on the scored days in time order and on the same hours shuffled. The longest run is the line to read."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.intervals import CAL_CUTOFFS, bounds, paired, total_of
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, SEED, show

df = mask_clock_changes(load(ALL30))[["unique_id", "ds", "y"]]
cal = total_of(paired(df, CAL_CUTOFFS))
# The three scored days are 72 hours back to back, so the sort puts them in time order.
sc = total_of(paired(df, pd.to_datetime(EVAL_CUTOFFS))).sort_values("ds")
lo, hi = bounds(sc, cal, 80)
missed = ~((sc["y"] >= lo) & (sc["y"] <= hi)).to_numpy()


def longest_run(m):
    """The most consecutive hours outside the band."""
    best = run = 0
    for x in m:
        run = run + 1 if x else 0
        best = max(best, run)
    return best


def miss_after_miss(m):
    """The share of missed hours, the last hour aside, whose next hour also misses."""
    return float(m[1:][m[:-1]].mean())


rng = np.random.default_rng(SEED)
# 10,000 orderings of the same hours: as many misses, with any order in time broken.
shuffles = [rng.permutation(missed) for _ in range(10_000)]
show("scored hours", len(missed), 0)
show("hours missed at 80", int(missed.sum()), 0)
show("longest run of missed hours", longest_run(missed), 0)
show("longest run of missed hours, shuffled, mean", np.mean([longest_run(s) for s in shuffles]), 1)
show("share of shuffles with a run this long", np.mean([longest_run(s) >= longest_run(missed) for s in shuffles]), 3)
show("misses followed by a miss", miss_after_miss(missed), 3)
show("misses followed by a miss, shuffled, mean", np.mean([miss_after_miss(s) for s in shuffles]), 3)
```

Output:

```text
scored hours: 72
hours missed at 80: 24
longest run of missed hours: 8
longest run of missed hours, shuffled, mean: 3.5
share of shuffles with a run this long: 0.002
misses followed by a miss: 0.478
misses followed by a miss, shuffled, mean: 0.324
```

The total's misses come in runs. The longest is 8 hours outside the band in a row. The same hours in shuffled order give a longest run of 3.5 on average, and only 0.002 of the shuffles reach one that long.

The hour after a miss points the same way, because it missed too in 0.478 of cases, against 0.324 once the order is broken. So report how misses persist beside the coverage, such as the longest run of missed hours, since a supplier short for several hours in a row pays for all of them before the next day's purchase can respond.

So the book promises nothing about coverage that it does not measure. The coverage in this chapter is what three days showed, under the calibration described in [Calibrate on earlier windows](#calibrate-on-earlier-windows).

**Working rule:** Report coverage on windows that the calibration never used, with the number of windows and the coverage of each. Keep the same measure in a running log once the forecast runs every day, as [Chapter 10](#keep-the-forecast-running) does. Read three scored days as a warning, not as a measurement of the level you were promised.

## Choose the level from the cost of error {#choose-the-level-from-the-cost-of-error}

The supplier buys one amount for each hour, and the costs of the two errors set that amount. Let `cu` be the cost of one kWh bought short and `co` the cost of one kWh bought and not used. Let `F` be the distribution of demand. Differentiating the expected cost with respect to the purchase `q` gives `co F(q) - cu (1 - F(q))`, which is zero where `F(q) = cu / (cu + co)`, the smallest expected cost. The level `cu / (cu + co)` is the critical fractile of the newsvendor model. The [HKUST IEEM 101 notes on the newsvendor model](https://ieda.ust.hk/dfaculty/ajay/courses/ieem101/lecs/inventory/newsvendor-proof.pdf) give the same proof, writing the cost of excess as `c0`. This chapter writes it `co`. The purchase is therefore the quantile at level `tau = cu / (cu + co)`.

With the illustrative costs from [Why one number is not enough](#why-one-number-is-not-enough), `tau` is 0.75. The rule says to buy the quantile of the demand at that level, for each hour. The quantile at level `tau` is the purchase that minimises the quantile loss at that level, as [Gneiting and Raftery (2007)](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf) show. The quantile loss is `tau * (y - q)` when the reading `y` is at or above the purchase `q`, and `(1 - tau) * (q - y)` when it is below. The quantile loss is not a cost in kWh or in money. It is the rule that the quantile minimises, and it has the same shape as the supplier's cost. Multiplying it by `cu + co` gives the cost exactly, which the example prints beside the mean cost.

Does buying at the critical fractile cost less than buying at the median or higher, on days the bands never saw? Below, the purchase is set for each hour from these costs, and the scored days answer the question. The level 0.95 is not offered, as [Measure coverage on held-out days](#measure-coverage-on-held-out-days) explains.

Example `buy-ahead-level-by-cost` (Python 3.13.16 · holidays 0.110.dev20261119030846 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.5 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.14:

```python
"""The buy level for the total, set from the two costs: the critical fractile, cu / (cu + co), is the quantile that minimises
the expected cost. Compare the mean cost and the hours short at each level; the costs are illustrative, not prices."""
import pandas as pd

from lib.electricity import load
from lib.intervals import CAL_CUTOFFS, COST_EXCESS, COST_SHORT, buy_report, critical_fractile, paired
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
# Every clock-change hour (four changes, 2013 and 2014) is masked as NaN, as in every example of this chapter.
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
# Calibration on Dec 9 to 20, 2014; scored on the three standard cutoffs.
pairs_cal, pairs_sc = paired(df, CAL_CUTOFFS), paired(df, pd.to_datetime(EVAL_CUTOFFS))

show("cost of a kWh short", COST_SHORT)
show("cost of a kWh unused", COST_EXCESS)
# The quantile level cu / (cu + co), from the two costs printed above.
show("critical fractile", critical_fractile())
# buy_report returns the printed rows as (label, value, decimal places).
for label, value, digits in buy_report(pairs_cal, pairs_sc):
    show(label, value, digits)
```

Output:

```text
cost of a kWh short: 3.00
cost of a kWh unused: 1.00
critical fractile: 0.75
scored hours: 72
residuals per hour for the total: 12
highest coverage the total's residuals allow: 0.846
simulated coverage at 80, exchangeable errors: 0.682
mean absolute error of the total, calibration days: 2415.51
mean absolute error of the total, scored days: 2985.88
total coverage at 80: 0.667
total coverage at 80 with finite-sample levels, not used: 0.736
total coverage at 80 on 2014-12-29: 0.625
total coverage at 80 on 2014-12-30: 0.708
total coverage at 80 on 2014-12-31: 0.667
total mean absolute error on 2014-12-29: 2448.53
total mean absolute error on 2014-12-30: 2149.78
total mean absolute error on 2014-12-31: 4359.32
mean cost at 0.50: 5087.95
hours short at 0.50: 0.528
mean cost at 0.75: 3843.61
hours short at 0.75: 0.403
mean cost at 0.90: 3667.43
hours short at 0.90: 0.222
quantile loss at critical fractile, times both costs: 3843.61
mean hourly total bound from the total: 31983.95
mean hourly total bound from the sum of client bounds: 32388.77
hours short at critical fractile, sum of client bounds: 0.306
mean cost at critical fractile, sum of client bounds: 3729.17
```

The identity holds: multiplied by the sum of the two costs, the quantile loss at the critical fractile is 3843.61, the same as the mean cost at that level, 3843.61. The rule is correct as arithmetic.

| Level | Mean cost | Hours short |
| --- | --- | --- |
| 0.50 | 5087.95 | 0.528 |
| 0.75, the critical fractile | 3843.61 | 0.403 |
| 0.90 | 3667.43 | 0.222 |

The result on the scored days is less comfortable. The rule chose the critical fractile, and on these three days 0.90 cost less, at 3667.43 against 3843.61. At the critical fractile the purchase was short in 0.403 of the hours, where a calibrated level would fall short in one hour in four. That is the coverage shortfall from [Measure coverage on held-out days](#measure-coverage-on-held-out-days) seen as money. We do not move the level to 0.90. The three scored days are the test, and a level chosen because it wins on them has been chosen on the test. The honest reading is that the bands were too narrow here, so the purchase was too low, and that the level is right only when the bands are.

Should the purchase follow the clients' bounds instead? Summing each client's bound at the critical fractile gives a bound of 32388.77 kWh an hour, against 31983.95 from the total's own residuals. Summed quantiles equal the total's quantile when the errors move together perfectly. For an upper quantile, with errors that partly cancel, the sum usually sits above it, as it does here.

On the scored days the summed bound did better, with hours short at 0.306 against 0.403, and a mean cost of 3729.17 against 3843.61. That advantage comes from its higher level, not from a better calibration, and the scored days cannot show that it holds in general. We keep the total's own bound, because the purchase is made against the total's residuals, and we do not switch to the bound that did better here.

**Working rule:** Set the buy level from the two costs, as `tau = cu / (cu + co)`, fix it before you score the days, and calibrate the total's bands on the total's own residuals. Show the realised cost at other levels as a check, but never move the level to whichever one would have won on the days you score.

## What goes wrong in production {#what-goes-wrong-ch8}

- **The calibration season is not the scored season.** Holidays are kept out of the calibration, which keeps the test honest, but the total's errors vary from one window to another, and they can be larger in the scored days than in the calibration windows. A band calibrated in a calm period misses a harder one. Notice it by comparing coverage with the nominal level every day and watching the running average. A coverage that falls below its label for a week is the sign, and the errors of that week are the first place to look.
- **Pooled bands hide clients.** Bands pooled in kWh are set by the largest clients. With unscaled residuals, the largest client's bands cover 0.000 of its hours at 80. With scaled residuals the lowest client coverage at 80 is 0.472, so even the scaled pool hides a client that misses. Read coverage per client, not only the pooled figure.
- **Three days say little.** A coverage figure from three scored days can look like a finding, but it is three observations of the day-level error. Use the coverage over many windows, and treat a short run as a reason to look, not as a result.
- **Dependence breaks the simple guarantee.** Hourly load is autocorrelated, and the calibration residuals of neighbouring hours are not independent. The bands carry no guarantee from the textbook theorem. Their coverage can drift when the weather or the calendar changes, and only the measured coverage tells you when that happens. A run of days whose errors share a sign is the pattern to watch for, and the running log is where it shows up.
- **The total has few residuals per hour.** A calibration window gives one residual for the total in each hour, so twelve windows give twelve. With signed residuals, the highest coverage twelve residuals allow is 0.846, so the total's bands stop at 80, and a level check should come before any band is offered. More calibration windows would give the total a larger sample, but each must be an ordinary day before the scored week.
- **Rolling calibration can use the days you score.** The built-in rule in [Build intervals from residuals](#build-intervals-from-residuals) calibrates each cutoff on the three cutoffs before it. In operation that is fine, because those readings are known. In a test, it makes the scored windows depend on each other. Keep the calibration set fixed and earlier than every scored window.

## Decisions this chapter made {#decisions-ch8}

- **Calibration windows.** Twelve ordinary days, Dec 9 to 20, 2014, before the held-out week. Holidays are excluded, and no calibration hour is scored. The decision windows use twelve days too, Nov 9 to 20, 2014. The length is a choice, not a result: the data do not show that twelve days is the best length.
- **Scale before pooling.** Each client's residuals are divided by its seasonal naive error on the history before the first calibration cutoff, the same scale the book uses for MASE. The decision windows settled it, and the total needs no scale.
- **No finite-sample correction in the bands.** The correction was tested on the decision windows, for the clients and for the total, and it did not improve the interval score. It is used only to read off which levels a set of residuals can support.
- **Signed residuals.** The bands and the purchase quantile use signed residuals, so the lower and upper bounds need not be symmetric. mlforecast's conformal methods use absolute residuals and give symmetric bands. The built-in run in [Build intervals from residuals](#build-intervals-from-residuals) is there for comparison.
- **The purchase is for the total.** The buy level and its quantile are set on the total's residuals. The clients' bands are for reading the forecasts, not for buying.
- **The costs are assumptions.** The costs of 3.00 and 1.00 are stated in [Why one number is not enough](#why-one-number-is-not-enough), as judgement, and not measured.
- **The statistical library's interval class.** statsforecast's class is `ConformalIntervals`. Its name differs from mlforecast's `PredictionIntervals`, and this chapter uses each name for its own library.
- **A third example.** The purchase decision needed its own measurement, so `buy-ahead-level-by-cost` was added, along with `conformal-decision-windows`, which makes the design choices on windows the held-out evaluation does not use.
- **Holiday coverage is not claimed.** Dec 25, 2014 is in the held-out week, but it is outside both the calibration and the scored windows. The book reports nothing about how the bands cover the holiday itself.
- **Bands before levels.** A purchase level is only as good as the band under it, and a band only as good as the windows that set it.
