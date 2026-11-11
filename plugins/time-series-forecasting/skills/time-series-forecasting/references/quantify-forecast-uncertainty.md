---
title: "Time Series Forecasting"
chapter: "Quantify forecast uncertainty"
chapter_id: quantify-forecast-uncertainty
book: time-series-forecasting
edition: 2026.11.3
verified: 2026-11-11
edition_code: PAPV-2BKC
canonical: https://rollingedition.com/time-series-forecasting/quantify-forecast-uncertainty
license: CC BY 4.0
attribution: "“Quantify forecast uncertainty,” chapter 8 of Time Series Forecasting, Edition 2026.11.3, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/quantify-forecast-uncertainty. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Quantify forecast uncertainty

By the end of this chapter you can attach prediction intervals to a day-ahead forecast, calibrate them on days that come before the days you score, measure how often they hold, and choose the level to buy at from the two costs of an error.

## Why one number is not enough {#why-one-number-is-not-enough}

The forecasts so far give one number for each client and hour. The supplier cannot buy an expected value. It buys power a day ahead, for the total of its clients, and each kWh it buys is either used or not. Buying short means buying the rest later at a premium. Buying long means paying for power that nobody uses. The two errors cost different amounts, so the right purchase is usually not the forecast itself. Take one hour. Suppose the forecast is 100 kWh. If the reading turns out 10 kWh higher, the supplier is short and pays the short cost on those 10 kWh. If it turns out 10 kWh lower, the supplier has 10 kWh it pays for and does not use. When the short cost is three times the unused cost, a purchase above the forecast costs less on average, because it makes the expensive error less likely. How far above the forecast the purchase should sit depends on that ratio, and on how wide the errors are.

This chapter states two costs as assumptions. A kWh bought short costs 3.00 cost units, and a kWh bought and not used costs 1.00. These numbers are illustrative. They are not prices, and the book does not claim that any real supplier faces them. [Section 5](#choose-the-level-from-the-cost-of-error) shows how they set the purchase.

A prediction interval gives a lower and an upper bound for each hour. Its level, such as 80 or 95, is the share of readings the bounds should contain. That share is the coverage, and coverage belongs to many forecasts made the same way, not to one. One day's band either contains the readings or it does not. Across the 72 hours of three days, the share inside the band is a measurement. Across a year of days, it becomes a track record. A 95 percent band whose hours fall inside it 90 percent of the time has undercovered, but no single day shows it. Only the average over many hours shows it, and that average is what we measure.

Quantiles connect the bands to the costs. The lower bound of a central 80 percent interval is the 0.1 quantile of the forecast's distribution, the value that the reading falls below one time in ten. The upper bound is the 0.9 quantile. The purchase that minimises the expected cost is also a quantile, and [section 5](#choose-the-level-from-the-cost-of-error) derives which one.

In the case, the range that matters is the total's, because the total is what the supplier buys. Chapter 6 forecast the thirty clients with one global model, and the total is the hourly sum of those forecasts. Each client has its own range, but the total's range cannot be read off the clients' ranges by adding them. [Section 5](#choose-the-level-from-the-cost-of-error) compares the two.

**Working rule:** Ask for a range wherever the costs of the two errors differ, and choose its level from those costs rather than from a number that looks reassuring. Report coverage as the share of hours inside the band over many windows, never as the chance that one day falls inside.

## Build intervals from residuals {#build-intervals-from-residuals}

A range needs bounds, and the simplest bounds come from past errors. A residual is the error of an earlier forecast: the reading minus the forecast, `e = y - f`. Conformal prediction builds a band from the residuals of forecasts made the same way on earlier days. Take the residuals of a set of calibration windows, group them by horizon step, and read off the quantiles you need. A day-ahead forecast made at 00:00 has one horizon step for each hour of the day, so the group is the hour alone. For a level `L` in percent, the bounds for a forecast `f` made at a given step are:

```text
lower = f + Q((1 - L/100) / 2)
upper = f + Q((1 + L/100) / 2)
```

where `Q(p)` is the empirical p-quantile of the calibration residuals at that step. The method assumes no model of the errors. It only assumes that the calibration residuals resemble the residuals to come, which [section 3](#calibrate-on-earlier-windows) tests. A calibration window is a cutoff whose residuals size the bands. It always comes before the cutoffs being forecast, and it is never one of the windows that are scored.

The library that does this for the book's model is mlforecast, at version 1.1.0. Its class `PredictionIntervals` takes a number of windows, a horizon and a method, and it has four conformal methods: `conformal_error`, `conformal_distribution`, and their weighted versions. The two unweighted methods score the absolute residuals, `|y - f|`, so their bounds are symmetric around the forecast (mlforecast 1.1.0, `mlforecast/conformal_prediction.py`, function `compute_conformity_scores`). The default, `conformal_distribution`, works one client and one horizon step at a time. For each client and step it takes the calibration windows' absolute residuals, makes the paths of the forecast plus and minus each one, and reads the quantiles of those paths. Nothing is pooled across clients. The statistical library, statsforecast at version 2.1.1, names its interval class `ConformalIntervals`, not `PredictionIntervals`.

The first example uses mlforecast's class with three calibration windows, and scores the three standard evaluation cutoffs: Dec 29, Dec 30 and Dec 31, 2014, each at 00:00. The three days are the held-out week's last three days, and they are the days this chapter scores. The example refits the global model at each cutoff. mlforecast calibrates each cutoff on the three cutoffs before it.

Example `conformal-three-windows` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""mlforecast's own conformal intervals, with three calibration windows, on the three standard cutoffs. Each cutoff is
refitted, and its intervals are calibrated on the three cutoffs before it. The coverage falls short of the level, and the
design, three residuals per client and hour, caps what the bands can cover."""
import pandas as pd

from lib.electricity import load
from lib.intervals import builtin_intervals, design_coverage, symmetric_ceiling
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cv = builtin_intervals(df, pd.to_datetime(EVAL_CUTOFFS))

show("scored hours", len(cv))
show("calibration windows per cutoff", 3)
show("residuals per client and hour", 3)
show("highest coverage three windows allow, any level", symmetric_ceiling(3), 3)
for level in (80, 95):
    show(f"simulated coverage at {level}, exchangeable errors", design_coverage(level, 3, "builtin"), 3)
for level in (80, 95):
    lo, hi = cv[f"LGBMRegressor-lo-{level}"], cv[f"LGBMRegressor-hi-{level}"]
    inside = (cv["y"] >= lo) & (cv["y"] <= hi)
    show(f"coverage at {level}", inside.mean(), 3)
    show(f"mean width at {level}", (hi - lo).mean())
    if level == 80:
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

The output is the failure, and it comes before any fix. At the 80 level the bands cover 0.690 of the 2160 client-hours, and at the 95 level they cover 0.750. Both fall short of their labels. The bands are 281.07 kWh wide on average at 80 and 355.39 kWh at 95.

The design sets a ceiling. With three windows, each client and hour has three absolute residuals, and the band reaches no further than the largest of them. For exchangeable errors, the test error is the largest of four absolute errors one time in four, so the band misses it that often. The highest coverage three windows allow is therefore 0.750, at any level. The 95 result sits on that ceiling. Under the same exchangeable assumption, the band's expected coverage is 0.656 at 80 and 0.732 at 95. The simulation draws normal errors, with the same construction. The measured figures are a little above those expected values, so the calibration days did not have smaller errors than the scored days. Calm calibration days would push coverage below the expected value, not above it. The shortfall is the construction's.

The coverage by day shows where the shortfall sits. At the 80 level it is 0.756 on Dec 29, 0.676 on Dec 30 and 0.637 on Dec 31. The forecast errors on those days were 114.62, 94.42 and 163.37 kWh on average. Dec 31 has the largest errors, but it is not the day with the lowest coverage, and three days cannot separate day-to-day variation from the design.

A second problem comes from the calibration. Each cutoff calibrates only on days before it: the bands for Dec 31 use Dec 28, 29 and 30. But Dec 29 and Dec 30 are scored days too. So the three scored windows are not independent, because one window's calibration contains the readings of another scored window. No band uses its own day's readings, and the rule is right for operation, where those readings are known. For a test it weakens the result. Fixing it would need a separate calibration fit for each cutoff, which is more than a one-argument change, so the chapter's own bands use a fixed calibration set instead, as [section 3](#calibrate-on-earlier-windows) shows.

**Working rule:** Build each band from the residuals of windows that come before its cutoff, and check the coverage it reaches on windows it did not use before you trust it. Read the level a design can reach before you read the coverage. Three residuals per client and hour cannot reach either label, so the fix is a larger calibration set, not a different reading of the output.

## Calibrate on earlier windows {#calibrate-on-earlier-windows}

The calibration windows must come before the windows you score, and they must not share a target hour with them. The book adds one more rule: a calibration window must not fall on a Portuguese public holiday, because a holiday's load follows the calendar rather than the week before it. The rule applies to the decision windows as well. The held-out evaluation calibrates on twelve ordinary days, Dec 9 to 20, 2014, which end four days before the held-out week. The example checks that no calibration hour is a holiday and none is shared with the scored week.

Twelve windows with thirty clients give 360 residuals for each hour of the day. They come from twelve days, though, and the thirty clients share each day's weather and calendar. So a day-level error is still a sample of twelve. The pooled residuals have a second problem. The clients differ enormously in size. In the scored week the largest client, MT_370, averages 17499.81 kWh an hour over the three scored days. Pooled residuals in kWh are dominated by such clients, so the bands fit the large clients and misfit the small ones. The fix is to divide each client's residuals by that client's scale before pooling, and multiply the bound back by the scale of the client being forecast. The scale is the seasonal naive error on the history before the first calibration cutoff, the same kind of scale the book uses for MASE. With the scale, the thirty clients count alike.

Two choices in this design were made on the decision windows, not on the held-out evaluation. The decision windows are the four cutoffs from Nov 25 to Dec 3, 2014. Their calibration is Nov 9 to 20, 2014, twelve holiday-free days that end four days before the first decision cutoff, the same shape as the held-out design. The windows are scored on their own, and the held-out evaluation is not read.

Example `conformal-decision-windows` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""The two choices of the calibration design, decided on the four decision windows before the held-out week: scaling each
client's residuals before they are pooled, and the finite-sample levels. The calibration is Nov 9 to 20, 2014, twelve
holiday-free days, and the scored windows are the decision cutoffs, Nov 25 to Dec 3, 2014. The standard cutoffs are not read."""
from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.intervals import DECISION_CAL, bounds, calibration_facts, coverage, interval_score, paired, total_of
from lib.panel import ALL30, DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.scoring import book_scale
from lib.settings import show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cal, sc = paired(df, DECISION_CAL), paired(df, DECISION_CUTOFFS)
scale = seasonal_scale(book_scale(raw, DECISION_CAL[0]))

for label, value in calibration_facts(df, DECISION_CUTOFFS, DECISION_CAL).items():
    show(label, value)
show("residuals per hour of the day", len(cal) // 24)
variants = (("unscaled", None, False), ("scaled", scale, False),
            ("unscaled, finite", None, True), ("scaled, finite", scale, True))
for name, s, fin in variants:
    for level in (80, 95):
        lo, hi = bounds(sc, cal, level, scale=s, finite=fin)
        show(f"{name}, coverage at {level}", coverage(sc["y"], lo, hi), 3)
        show(f"{name}, interval score at {level}", interval_score(sc["y"], lo, hi, level))
    lo, hi = bounds(sc, cal, 80, scale=s, finite=fin)
    show(f"{name}, lowest client coverage at 80", ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean().min(), 3)
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

The decision windows settle the scale first. With the scale, the coverage at 80 of the worst-covered client rises from 0.021 to 0.365, and the interval score at 80 falls from 603.88 to 336.72. At 95 it falls from 1950.32 to 581.28. The pooled coverage at 80 is closer to its label without the scale, at 0.809 against 0.834. We judged the variants by the interval score and the lowest client's coverage, because the pooled figure is the one that hides clients, as the scored days show below. We chose that measure after seeing the decision numbers, and the pooled figure is reported beside it for that reason. The scale stays.

The finite-sample levels settle the second choice. They move each quantile level to `floor((n + 1) * a) / n` for the lower bound and `ceil((n + 1) * (1 - a)) / n` for the upper, where `n` is the number of residuals and `a` the tail share. On the decision windows they change the scaled 80 coverage from 0.834 to 0.835, and they make the interval score worse at both levels: 337.31 against 336.72 at 80, and 592.35 against 581.28 at 95. The correction widens the bands and does not help, so the bands do not use it.

The held-out evaluation then reports the same design on the standard cutoffs.

Example `conformal-earlier-windows` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""Conformal bands for every client, calibrated on twelve holiday-free days before the scored week, with each client's
residuals scaled first. The example also prints unscaled, three-day and finite-sample variants, for comparison."""
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
scale = seasonal_scale(book_scale(raw, CAL_CUTOFFS[0]))
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
lo, hi = bounds(sc, cal, 80)
unscaled = ((sc["y"] >= lo) & (sc["y"] <= hi)).groupby(sc["unique_id"]).mean()
show("largest client coverage at 80, unscaled residuals", unscaled[big], 3)
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

The scaled bands cover 0.739 of client-hours at 80 and 0.902 at 95. Their mean widths are 267.62 kWh and 532.00 kWh. The interval score is a scoring rule for an interval. It adds the width to a penalty that grows with the distance by which a reading misses the band, scaled by 2 over the miss rate (Gneiting and Raftery, 2007, [eq. 43](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)). The score at 80 is 673.89 and at 95 it is 1326.80. The score is in kWh, so the large clients dominate it. Lower is better, and the score rewards a band that is both narrow and right.

The pooled bands still have to be read per client. The lowest client coverage at 80 is 0.472, for the client the scaled bands fit least well. With unscaled residuals the largest client is covered in 0.000 of its hours at 80. The pooled kWh bands were set by the large clients, and they miss the largest client entirely. The example prints that unscaled figure so the reader can see what the scale changes.

Two more checks test the design on the standard cutoffs. The first is the number of calibration windows: the three days nearest the scored week, Dec 18 to 20, give 0.711 at 80, against 0.739 with all twelve. Three days are a smaller sample, and the coverage is a little lower. The second is the finite-sample levels on the standard cutoffs, which give 0.741 at 80. That is a small change, and it agrees with the decision windows: the correction does little for the client bands.

**Working rule:** Calibrate on windows that come before the scored ones, with no holiday in them, and scale each client before pooling its residuals. Make each design choice on windows that are not the ones you report. Report how many windows and residuals went into the bands and the coverage they gave on the scored days, even when that coverage falls short of the level.

## Measure coverage on held-out days {#measure-coverage-on-held-out-days}

Coverage is measured on days that the calibration never used. The standard evaluation cutoffs give three days, and each day gives 24 hours for each client. The 2160 client-hours are not that many independent observations. The thirty clients share the calendar and the weather, so the hours of one day agree with one another. For day-level errors the sample is three days, and three days cannot measure a coverage level. They can show that a band fell short on those days. They cannot say by how much the band falls short over a longer period.

The supplier buys the total, so the total's coverage matters most. The total's bands are built from its own residuals over the same twelve days, with the quantiles read directly, and they are offered at 80 only. Twelve residuals cannot support 95. With signed bounds, the band from the smallest residual to the largest covers at most 0.846 of the time, if the residuals are exchangeable. A 95 band, or a 90 band, asks for more than that, so the chapter does not offer them for the total. The total's bands cover 0.667 of its 72 scored hours at 80. For exchangeable errors, the same construction covers 0.682, so most of the gap to 80 comes from the twelve-residual sample. The example that uses the bands is in [section 5](#choose-the-level-from-the-cost-of-error).

The total's errors vary by day. The mean absolute error of the total was 2415.51 kWh on the calibration days and 2985.88 kWh on the scored days. By day, the error was 2448.53 kWh on Dec 29, 2149.78 on Dec 30 and 4359.32 on Dec 31. Dec 31 accounts for most of the gap between the scored days and the calibration days. The coverage by day, 0.625 on Dec 29, 0.708 on Dec 30 and 0.667 on Dec 31, does not follow the errors: each day has 24 hours, and three days are too few to tell the two apart.

The finite-sample levels would change the total's figure. On the scored days they give 0.736 at 80. The choice was made on the decision windows, where the correction widened the total's bands and lowered their interval score, so the bands do not use it. The decision windows also show that the direction of the gap is not fixed. There the total's 80 bands covered 0.948 of hours, more than their label, and the finite levels pushed that to 0.990.

The guarantee that conformal prediction states is for a particular kind of data. Angelopoulos and Bates (2022, [arXiv](https://arxiv.org/pdf/2107.07511)) show that split conformal prediction covers the test point with probability at least `1 - alpha` when the calibration and test points are independent and identically distributed, or more generally exchangeable. They also note that adjacent points in a time series are not exchangeable, using a temperature series as the example. The same holds for hourly load: each hour carries the one before it, and a day's hours share the weather and the calendar. Barber and co-authors (2023, [arXiv](https://arxiv.org/abs/2202.13415)) call the loss in coverage when exchangeability fails a coverage gap. Their bound does not assume a particular joint distribution. It is small when recent calibration points are weighted in a way that matches the test point's distribution, as in slow drift. That result is theoretical, and this chapter does not test it. A 2026 preprint surveys conformal methods for dependent series ([arXiv](https://arxiv.org/abs/2601.18509)) and states that temporal dependence violates the exchangeability assumption. It is not peer reviewed, and we cite it only for that point.

So the book promises nothing about coverage that it does not measure. The coverage in this chapter is what three days showed, under the calibration described in [section 3](#calibrate-on-earlier-windows).

**Working rule:** Report coverage on windows that the calibration never used, with the number of windows and the coverage of each. Keep the same measure in a running log once the forecast runs every day, as Chapter 10 does. Read three scored days as a warning, not as a measurement of the level you were promised.

## Choose the level from the cost of error {#choose-the-level-from-the-cost-of-error}

The supplier buys one amount for each hour, and the costs of the two errors set that amount. Let `cu` be the cost of one kWh bought short and `co` the cost of one kWh bought and not used. Let `F` be the distribution of demand. Differentiating the expected cost with respect to the purchase `q` gives `co F(q) - cu (1 - F(q))`, which is zero where `F(q) = cu / (cu + co)`, the smallest expected cost. This is the critical fractile of the newsvendor model. The HKUST IEEM 101 lecture notes on the newsvendor model ([lecture notes](https://ieda.ust.hk/dfaculty/ajay/courses/ieem101/lecs/inventory/newsvendor-proof.pdf)) give the same proof, writing the cost of excess as `c0`. This chapter writes it `co`. The purchase is therefore the quantile at level `tau = cu / (cu + co)`.

With the illustrative costs from [section 1](#why-one-number-is-not-enough), `tau` is 0.75. The rule says to buy the quantile of the demand at that level, for each hour. The quantile at level `tau` is the purchase that minimises the quantile loss at that level (Gneiting and Raftery, 2007). The loss is `tau * (y - q)` when the reading `y` is at or above the purchase `q`, and `(1 - tau) * (q - y)` when it is below. The quantile loss is not a cost in kWh or in money. It is the rule that the quantile minimises, and it has the same shape as the supplier's cost. Multiplying it by `cu + co` gives the cost exactly, which the example checks.

Example `buy-ahead-level-by-cost` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.5.4 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.3:

```python
"""The buy level for the total, from the two costs. The critical fractile, cu / (cu + co), is the quantile that minimises
the expected cost. The example prints the costs, the total's 80 percent bands with their coverage by day, the realised cost
of three levels on the three standard cutoffs, and the total's bound against the sum of the clients' bounds. The costs are
illustrative; they are not prices."""
import pandas as pd

from lib.electricity import load
from lib.intervals import CAL_CUTOFFS, COST_EXCESS, COST_SHORT, buy_report, critical_fractile, paired
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
pairs_cal, pairs_sc = paired(df, CAL_CUTOFFS), paired(df, pd.to_datetime(EVAL_CUTOFFS))

show("cost of a kWh short", COST_SHORT)
show("cost of a kWh unused", COST_EXCESS)
show("critical fractile", critical_fractile())
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

The example prints the costs, the critical fractile and the total's bounds. It also prints the total's coverage by day, the mean absolute error of the total on the calibration and scored days, and the realised cost at three levels for the total: 0.50, the critical fractile and 0.90. The level 0.95 is not offered, because twelve residuals cannot support it. The mean cost at 0.50 is 5087.95, at the critical fractile 3843.61, and at 0.90 3667.43. The share of hours short falls from 0.528 at 0.50 to 0.403 at the critical fractile, and to 0.222 at 0.90.

The identity holds. The quantile loss at the critical fractile, multiplied by the sum of the two costs, is 3843.61, the same as the mean cost at the critical fractile. The rule is correct as arithmetic.

The result on the scored days is less comfortable. The rule chose the critical fractile, and on these three days 0.90 cost less. At the critical fractile the purchase was short in 0.403 of the hours, where a calibrated level would fall short in one hour in four. That is the coverage shortfall from [section 4](#measure-coverage-on-held-out-days) seen as money. We do not move the level to 0.90. The three scored days are the test, and a level chosen because it wins on them has been chosen on the test. The honest reading is that the bands were too narrow here, so the purchase was too low, and that the level is right only when the bands are.

The same question arises for the total's bound. A bound built by adding each client's bound at the critical fractile is higher than the total's own bound: 32388.77 kWh an hour against 31983.95. Summed quantiles equal the total's quantile when the errors move together perfectly. For an upper quantile, with errors that partly cancel, the sum usually sits above it, as it does here. On the scored days the summed bound did better: its share of hours short was 0.306 and its mean cost 3729.17, against 0.403 and 3843.61 for the total's bound. That advantage comes from its higher level, not from a better calibration, and three days cannot show that it holds in general. We keep the total's own bound, because the purchase is made against the total's residuals, and we do not switch to the bound that did better here.

**Working rule:** Set the buy level from the two costs, as `tau = cu / (cu + co)`, fix it before you score the days, and calibrate the total's bands on the total's own residuals. Show the realised cost at other levels as a check, but never move the level to whichever one would have won on the days you score.

## What goes wrong in production {#what-goes-wrong-ch8}

- **The calibration season is not the scored season.** Holidays are kept out of the calibration, which keeps the test honest, but the total's errors vary from one window to another, and they can be larger in the scored days than in the calibration days. A band calibrated in a calm period misses a harder one. Notice it by comparing coverage with the nominal level every day and watching the running average. A coverage that falls below its label for a week is the sign, and the errors of that week are the first place to look.
- **Pooled bands hide clients.** Bands pooled in kWh are set by the largest clients. The largest client's bands cover 0.000 of its hours at 80. With scaled residuals the lowest client coverage at 80 is 0.472, so even the scaled pool hides a client that misses. Read coverage per client, not only the pooled figure.
- **Three days say little.** A coverage figure from three scored days can look like a finding, but it is three observations of the day-level error. Use the coverage over many windows, and treat a short run as a reason to look, not as a result.
- **Dependence breaks the simple guarantee.** Hourly load is autocorrelated, and the calibration residuals of neighbouring hours are not independent. The bands carry no guarantee from the textbook theorem. Their coverage can drift when the weather or the calendar changes, and only the measured coverage tells you when that happens. A run of days whose errors share a sign is the pattern to watch for, and the running log is where it shows up.
- **The total has few residuals per hour.** A calibration window gives one residual for the total in each hour, so twelve windows give twelve. With signed residuals, the highest coverage twelve residuals allow is 0.846, so the total's bands stop at 80, and a level check should come before any band is offered. More calibration windows would give the total a larger sample, but each must be an ordinary day before the scored week.
- **Rolling calibration can use the days you score.** The built-in rule in [section 2](#build-intervals-from-residuals) calibrates each cutoff on the three cutoffs before it. In operation that is fine, because those readings are known. In a test, it makes the scored windows depend on each other. Keep the calibration set fixed and earlier than every scored window.

## Decisions this chapter made {#decisions-ch8}

- **Calibration days.** Twelve ordinary days, Dec 9 to 20, 2014, before the held-out week. Holidays are excluded, and no calibration hour is scored. The decision windows use twelve days too, Nov 9 to 20, 2014. The length is a choice, not a result: the data do not show that twelve days is the best length.
- **Scale before pooling.** Each client's residuals are divided by its seasonal naive error on the history before the first calibration cutoff, the same scale the book uses for MASE. The choice was made on the decision windows, and the total needs no scale.
- **No finite-sample correction in the bands.** The correction was tested on the decision windows, for the clients and for the total, and it did not improve the interval score. It is used only to read off which levels a set of residuals can support.
- **Signed residuals.** The bands and the purchase quantile use signed residuals, so the lower and upper bounds need not be symmetric. mlforecast's conformal methods use absolute residuals and give symmetric bands. The built-in run in [section 2](#build-intervals-from-residuals) is there for comparison.
- **The purchase is for the total.** The buy level and its quantile are set on the total's residuals. The clients' bands are for reading the forecasts, not for buying.
- **The costs are assumptions.** The costs of 3.00 for a short kWh and 1.00 for an unused kWh are stated, illustrative, and labelled as judgement. They are not measured.
- **A third example.** The purchase decision needed its own measurement, so `buy-ahead-level-by-cost` was added, along with `conformal-decision-windows`, which makes the design choices on windows the held-out evaluation does not use.
- **Holiday coverage is not claimed.** Dec 25, 2014 is in the held-out week, but it is outside both the calibration and the scored windows. The book reports nothing about how the bands cover the holiday itself.
- **The statistical library's interval class.** statsforecast's class is `ConformalIntervals`. Its name differs from mlforecast's `PredictionIntervals`, and this chapter uses each name for its own library.
