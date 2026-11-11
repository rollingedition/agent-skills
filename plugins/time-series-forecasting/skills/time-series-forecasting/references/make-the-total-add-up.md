---
title: "Time Series Forecasting"
chapter: "Make the total add up"
chapter_id: make-the-total-add-up
book: time-series-forecasting
edition: 2026.11.1
verified: 2026-11-11
edition_code: HK8M-ENSS
canonical: https://rollingedition.com/time-series-forecasting/make-the-total-add-up
license: CC BY 4.0
attribution: "“Make the total add up,” chapter 7 of Time Series Forecasting, Edition 2026.11.1, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/make-the-total-add-up. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Make the total add up

By the end of this chapter you can forecast the total of thirty clients two ways, choose between them on decision windows, and split the total into client shares using only history before each cutoff.

The supplier buys one amount of power a day ahead, and that amount is set against the total demand of its clients. Chapter 6 forecast each client. The total can be built from those forecasts, or forecast on its own. This chapter asks whether the two agree, and which one to trust. Both are scored on the same windows as before, so the comparison is fair. The examples use the clients, windows and scale of Chapter 6, so each number in this chapter is printed by an example that a reader can run.

## Why the total needs a check {#why-the-total-needs-a-check}

Two forecasts of one quantity can disagree, because they are made by different routes. Here the quantity is the total demand of the thirty clients (`ALL30`) in each hour. One route adds up thirty client forecasts. The other fits one model to the total series. Both read the same readings, but each fails in its own way. The sum carries every client's error into the total. The total model sees only the total's own pattern, and the clients' separate patterns can disappear inside it.

The check matters because the supplier buys against the total, not against each client. A total can miss even when every client is forecast well, if the clients' errors lean the same way in the same hour. The chapter therefore asks two questions, in order. First, do the parts add up to the whole in the data? Second, is a total forecast better than the sum of the parts on the windows that matter?

Forecasts that add up are called coherent. The textbook names several ways to make them so. Two of them are *bottom-up*, which forecasts the bottom level, here the clients, and sums the results, and *top-down*, which forecasts the top, the total, and splits it down by proportions ([Hyndman and Athanasopoulos, *Forecasting: Principles and Practice*, 3rd ed., chapter 11](https://otexts.com/fpp3/hierarchical.html)). This chapter uses the two names only in those senses.

Coherence is a constraint, not a measure of accuracy. A total that adds up can still be worse than one that does not. So this chapter scores the total and each client separately, and it never accepts a forecast because its parts agree.

The book builds both totals by hand, in pandas, rather than with `hierarchicalforecast`. The hierarchy has one level, so each route is one sum or one split, and the runtime stays small. A method that combines the two routes optimally does exist. MinT chooses the coherent forecasts that minimise the mean squared error of the coherent forecasts, under an unbiasedness assumption, and it uses the covariance matrix of the forecast errors ([Wickramasuriya, Athanasopoulos and Hyndman, 2019](https://doi.org/10.1080/01621459.2018.1448825); the open working paper is at [robjhyndman.com/papers/mint.pdf](https://robjhyndman.com/papers/mint.pdf)). Estimating that matrix is a project of its own, and this chapter does not take it on.

**Working rule:** Forecast the total both ways whenever a decision depends on it. Score both on the same windows, against the total and against each client. Keep the method that wins on the decision windows, and never accept a total because its parts add up.

## Sum the client forecasts {#sum-the-client-forecasts}

The bottom-up total is the sum, hour by hour, of the thirty client forecasts that Chapter 6 made. For each cutoff, one global model forecasts every client for the next 24 hours, with lags 24 and 168 and the client identifier that Chapter 6 kept. The total's forecast for an hour is the sum of the thirty values for that hour. With `c` a client and `t` an hour, the rule is `total(t) = sum over c of forecast(c, t)`.

The sum adds up by construction, so the check that matters is on the data. The total series has to equal the sum of the thirty readings in every hour, or every score is measured against the wrong number. The exception is the clock-change hours. A clock-change flag sets a client's reading to missing, so the total is missing at 01:00 on Mar 31, 2013 and Mar 30, 2014, the gap hours, and at 01:00 on Oct 27, 2013 and Oct 26, 2014, the repeat hours.

Example `total-bottom-up-and-direct` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Forecast the total of the thirty clients two ways: bottom-up, the sum of the client forecasts, and direct, one model on
the total. Choose the method, and the direct model's target scaling, on the four decision windows by MAE on the total.
Then report both methods on the three standard cutoffs beside seasonal naive, on the total's MASE scale. The last lines
check the total against its parts and the scale against readings after each scored cutoff."""
import pandas as pd

from lib.baselines import seasonal_scale
from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours
from lib.scoring import actual_hours, score_windows
from lib.settings import EVAL_CUTOFFS, show
from lib.totals import (DIRECT_SCALED, METHODS, TOTAL, direct_windows, plain_mae, pooled_mae, total_checks,
                        total_forecasts, total_frame, total_scale_rows)

raw = load(ALL30)
total = total_frame(raw)
dec, cut = pd.to_datetime(DECISION_CUTOFFS), pd.to_datetime(EVAL_CUTOFFS)

dec_actual = actual_hours(total, dec)
dec_mae = pooled_mae(dec_actual, total_forecasts(raw, dec), ["bottom-up", "direct"])
direct_setting = {s: pooled_mae(dec_actual, direct_windows(raw, dec, scaled=s), ["direct"])["direct"]
                  for s in (True, False)}
if direct_setting[DIRECT_SCALED] != min(direct_setting.values()):
    raise ValueError("DIRECT_SCALED is not the target setting with the lower MAE on the decision windows")
show("decision cutoffs", len(dec))
show("decision holiday hours", check_decision_hours(dec_actual))
show("MAE bottom-up, decision windows", dec_mae["bottom-up"])
show("MAE direct, decision windows", dec_mae["direct"])
show("MAE direct with a scaled target, decision windows", direct_setting[True])
show("chosen direct target", "unscaled" if not DIRECT_SCALED else "scaled")
show("MAE bottom-up without identifier, decision windows", plain_mae(raw, dec))
show("chosen total method", dec_mae.idxmin())

scale = total_scale_rows(raw, cut[0])
scored, per_client = score_windows(actual_hours(total, cut), total_forecasts(raw, cut), METHODS, scale)
show("scored hours", len(scored))
show("MASE scale of the total", seasonal_scale(scale)[TOTAL])
for model in METHODS:
    show(f"MAE {model}", (scored["y"] - scored[model]).abs().mean())
for model in METHODS:
    show(f"MASE {model}", per_client.loc[TOTAL, model])
show("MAE bottom-up without identifier", plain_mae(raw, cut))
for label, value in total_checks(raw, cut[0], cut).items():
    show(label, value)
```

Output:

```text
decision cutoffs: 4
decision holiday hours: 0
MAE bottom-up, decision windows: 1267.47
MAE direct, decision windows: 1678.62
MAE direct with a scaled target, decision windows: 1705.71
chosen direct target: unscaled
MAE bottom-up without identifier, decision windows: 1383.29
chosen total method: bottom-up
scored hours: 72
MASE scale of the total: 2689.26
MAE SeasonalNaive: 3639.41
MAE bottom-up: 2985.88
MAE direct: 3423.11
MASE SeasonalNaive: 1.35
MASE bottom-up: 1.11
MASE direct: 1.27
MAE bottom-up without identifier: 2837.66
clock-free hours where the total differs from the sum of the thirty clients: 0
scale changes after poisoning readings from each scored cutoff: 0
```

The example builds both totals and runs its checks at the end. The first check compares the total with the sum of the thirty readings in every hour that has no clock-change flag. It finds 0 hours that differ.

The clock-change hours need one more rule. The total is missing in those hours, but the forecast is not. Each forecast window still produces a value for every labelled hour, so the output grid has no holes that a downstream table would have to fill. The scoring refuses a forecast hour that has no reading, so a masked hour cannot be scored as a zero. No scored window in this chapter holds one.

The start rule applies to each client before the sum. A late starter's zeros before its first reading are not demand, so the rule drops them, as Chapter 4 showed for one client. The rule does not change the total, because a zero adds nothing to a sum, and a client that has not started contributes nothing either. The check above shows it. The rule does change each client's own forecast, because a model fitted on those zeros would learn them as low use.

The bottom-up total inherits the clients' errors, good and bad. Chapter 6 found that the model beats seasonal naive for 23 of the thirty clients on the standard cutoffs, and does worse for the rest. The comparison below measures how much of that error reaches the total.

Only means add. The mean of a sum is the sum of the means, because expectation is linear. The median of a sum is not, in general, the sum of the medians, and the same holds for other quantiles. They add only in special cases, such as errors that move together perfectly. So the bottom-up total is a point forecast. A range for the total cannot be built by adding the clients' ranges. Chapter 8 returns to this for the intervals.

**Working rule:** Sum the client forecasts hour by hour, after checking that the total series equals the sum of its readings in every hour without a clock-change flag. Apply the start rule to each client before the sum, so no client's model is fitted to its zeros. Treat the sum as a point forecast, and do not take the sum of the clients' medians as the median of the total.

## Forecast the total directly {#forecast-the-total-directly}

The direct total is one model fitted to the total series itself. Its history is the total's history before the cutoff: the readings of the 1,344 hours before it, which is 8 weeks, the same length as the clients' histories. Each client's history is cut by the start rule, its clock-change hours are filled from its own neighbours, as Chapter 3 does, and the readings are summed by hour. The total's history therefore has no missing hour.

The model uses the features the clients use. Its inputs are the total's readings 24 and 168 hours earlier, so no input comes from the day being forecast. Its target is the total as it is, not scaled. Chapter 6 scales each client's target, because one model over clients of different sizes would otherwise fit the large ones. A single total has no such mix, so that reason does not carry over. The example fits both settings and compares them on the decision windows, and the unscaled target has the lower error, so the direct model uses it. The model is fitted once per cutoff, on that cutoff's history only, and it forecasts the next 24 hours. It is a LightGBM regressor inside mlforecast 1.1.0, with the settings of Chapter 5.

The two totals differ in how they are built. The bottom-up total comes from one global model that forecasts every client, and the direct total from one model that forecasts the sum. The lags and the other settings are the same. The target scaling differs, and the decision windows choose it for the direct model alone.

The total is usually smoother than any client, because the clients' peaks partly cancel in the sum. A model fitted to a smoother series has less of its own noise to learn, which can help the direct total. The comparison below tests whether it does on these windows, and the answer is not the one the smoothness suggests.

The model sees the total only through its history. It does not see which client a reading came from, or which client moved the total. That is the trade the direct method makes. It gets one smooth series and loses the clients' separate shapes. The bottom-up method keeps those shapes and must add thirty errors together.
Seasonal naive on the total is the baseline that both must beat. It forecasts each hour as the same hour the day before, as in Chapter 2, applied to the total's history. It is scored on the same windows and against the same scale.

**Working rule:** Forecast the total directly with the clients' features, from the total's own history before each cutoff, and choose the target's scaling on the decision windows. Use the same windows for both methods, and score each against seasonal naive on the total. Report both methods, and not only the one you built.

## Compare the two totals {#compare-the-two-totals}

The choice between the two methods is made on the four decision windows, which are ordinary days before the held-out week and are used only to choose: Nov 25, Nov 26, Dec 2 and Dec 3, 2014. [Chapter 6](#score-thirty-clients-on-the-same-cutoffs) chose the client identifier on the same days. Each method is scored by mean absolute error (MAE) on the total. On the decision windows the [bottom-up total](#sum-the-client-forecasts) has an MAE of 1267.47 kWh, against 1678.62 kWh for the [direct total](#forecast-the-total-directly), so the bottom-up total is chosen. The direct total's target is unscaled because that setting has the lower error there: 1678.62 kWh, against 1705.71 kWh with the target scaled. The example refuses to run if a decision hour falls on a Portuguese holiday, and it counts 0 such hours.

The standard cutoffs, Dec 29, 30 and 31, 2014, are the report. They are not used to choose. On these three windows the total has 72 scored hours. Its MASE scale is the mean absolute change between readings a day apart, taken over every reading before Dec 29, 2014, with the clock-change hours masked. That is the rule for a MASE scale from [Chapter 2](#take-the-mase-scale-from-history), as [Chapter 6](#score-thirty-clients-on-the-same-cutoffs) applies it to each client, here applied to the total, and it comes to 2689.26 kWh.

| Method | MAE (kWh) | MASE |
| --- | --- | --- |
| Seasonal naive | 3639.41 | 1.35 |
| Bottom-up | 2985.88 | 1.11 |
| Direct | 3423.11 | 1.27 |

MAE and MASE rank the methods alike here. MAE is in kilowatt-hours, so it reads as the average cost of an hour's error. MASE divides each error by the same scale, so on one series it is only a constant multiple of MAE. Its use is across series. Chapter 6 needs it to compare clients of very different sizes, and the total's score sits beside theirs on the same footing.

Bottom-up has the lower error on both window sets. On the standard cutoffs its MASE is 1.11, against 1.27 for the direct total and 1.35 for seasonal naive. The direct total beats seasonal naive on the total, but by a smaller margin than the bottom-up total does.

A method wins on the decision windows when its error is lower there, and the standard cutoffs then either confirm that or contradict it. For the total, the standard cutoffs confirm the choice: bottom-up is lower on both window sets. That agreement is the reason the chapter can recommend bottom-up for the total with some confidence. Agreement counts only when the two sets are separate, and they are. The four decision days all fall before Dec 25, 2014, the first day of the held-out week, and the standard cutoffs are the last three days of that week. No decision reads a standard cutoff.

The identifier is where the two window sets disagree. On the decision windows, the bottom-up total without the identifier has an MAE of 1383.29 kWh, against 1267.47 kWh with it, so the identifier lowers the total's error there, as the per-client MASE in Chapter 6 does on the same windows. On the standard cutoffs the plain total has an MAE of 2837.66 kWh, and the total with the identifier has 2985.88 kWh. The standard cutoffs therefore favour the plain total. The book reports that and does not act on it: Chapter 6 kept the identifier on per-client MASE, and the decision windows are the ones that choose. A supplier that doubts four decision windows should add decision windows before Dec 25, 2014, and decide again on those, not on the standard cutoffs.

**Working rule:** Choose a method on the decision windows, by the measure you will report. Report the same measure on the standard cutoffs beside seasonal naive, with the scored hours and the scale. When two window sets disagree, report both, say how far apart they are, and do not pick the one that reads better.

## Split a total by share {#split-a-total-by-share}

The top-down split starts from the [direct total](#forecast-the-total-directly) and gives each client a share of it. A client's share is its readings over its own history, the 1,344 hours before the cutoff, divided by the total's readings over the same hours. The shares add to 1 by construction. Each client's top-down forecast for an hour is the direct total's forecast for that hour, times its share. A client that supplied a tenth of the total over the past 8 weeks is expected to take a tenth of the total the next day.

The eight weeks are a choice, not a tuned value. They are the history every other model in this chapter reads, so the split uses the same memory as the clients. A shorter window would follow a change in a client's share sooner, and it would be noisier. This chapter does not measure that trade-off. A supplier that wants it should test it on the decision windows, the way the choice of method is tested here.

The weak point is the shape of the day. The split gives every client the total's daily profile. A client that peaks at a different hour gets the wrong profile in every hour, however good the total forecast is. One more check, which this chapter calls the oracle check, applies the shares to the actual total, which no forecast can know. Its mean per-client MAE is 171.80 kWh. It is a reference, not a method: it gives the error the split would have with a perfect total. The bottom-up forecast, which has to forecast each client, has a mean per-client MAE of 122.81 kWh. On these clients the split loses even with the true total in hand. The shares are also uneven. On the first cutoff, Dec 29, 2014, the largest client's share of the total is 0.56.

The working paper that defines MinT reports, citing Hyndman et al. (2011), that a top-down split biases the reconciled forecasts at each level, even when the base forecasts are unbiased ([Wickramasuriya, Athanasopoulos and Hyndman, 2017](https://robjhyndman.com/papers/mint.pdf)). This chapter does not re-derive that result. It measures the split on these clients, and the oracle check gives a reference for the split's own error.

Example `total-split-by-share` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Split the direct total forecast into client forecasts by each client's share of the history before its cutoff (top-down),
and compare each client with the bottom-up forecast. Choose the per-client method on the decision windows by mean
per-client MASE, then report both on the standard cutoffs. The check tests that no share moves when readings after its
cutoff change."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours
from lib.settings import EVAL_CUTOFFS, show
from lib.totals import SPLIT_METHODS, client_mae, oracle_split_mae, shares, split_checks, split_scored

raw = load(ALL30)
dec, cut = pd.to_datetime(DECISION_CUTOFFS), pd.to_datetime(EVAL_CUTOFFS)

dec_scored, dec_per, _ = split_scored(raw, dec)
show("decision holiday hours", check_decision_hours(dec_scored))
show("mean per-client MASE bottom-up, decision windows", dec_per["bottom-up"].mean())
show("mean per-client MASE top-down, decision windows", dec_per["top-down"].mean())
show("chosen client method", dec_per.mean().idxmin())

scored, per_client, _ = split_scored(raw, cut)
show("scored hours", len(scored))
mae = pd.DataFrame({m: client_mae(scored, m) for m in SPLIT_METHODS})
for model in SPLIT_METHODS:
    show(f"mean per-client MAE {model}", mae[model].mean())
for model in SPLIT_METHODS:
    show(f"mean per-client MASE {model}", per_client[model].mean())
show("clients where top-down has the lower MAE", int((mae["top-down"] < mae["bottom-up"]).sum()))
show("mean per-client MAE with the true total split by share", oracle_split_mae(raw, cut))
show("largest client share of the total, first cutoff", shares(raw, cut[0]).max())
for label, value in split_checks(raw, cut).items():
    show(label, value)
```

Output:

```text
decision holiday hours: 0
mean per-client MASE bottom-up, decision windows: 0.75
mean per-client MASE top-down, decision windows: 2.37
chosen client method: bottom-up
scored hours: 2160
mean per-client MAE bottom-up: 122.81
mean per-client MAE top-down: 218.95
mean per-client MASE bottom-up: 0.91
mean per-client MASE top-down: 2.59
clients where top-down has the lower MAE: 0
mean per-client MAE with the true total split by share: 171.80
largest client share of the total, first cutoff: 0.56
shares changed after poisoning readings from their cutoff: 0
```

The example makes the choice on the decision windows first. The mean per-client MASE is 0.75 for bottom-up and 2.37 for top-down, so bottom-up is chosen for the clients. On the standard cutoffs it scores 2160 client hours. The mean per-client MAE is 218.95 kWh for top-down and 122.81 kWh for bottom-up. The mean per-client MASE is 2.59 against 0.91, and top-down has the lower MAE for 0 of the thirty clients. Chapter 6's pooled MAE for the same forecasts is 122.81 kWh, the same as the bottom-up figure above. That is no accident: every client has the same 72 scored hours, so the mean of the client errors equals the pooled error.

A share must read only the history before its cutoff, so the split is checked for leakage. The check changes every reading from each cutoff on, once to zero and once to a very large value, and recomputes the shares. Across the six comparisons (three cutoffs by two values), the count of comparisons in which a share changes is 0. If any share had read a reading after its cutoff, the large value would have entered it. The shares add to 1, and the top-down clients add up to the direct total in every hour, by construction. An identity like that cannot fail, so the chapter does not count it. The leak check is the test that can fail, and it is the one counted.

**Working rule:** Split a total by share only as a baseline, or when the clients' daily profiles are alike. Compute each share from the history before its cutoff, check that no share moves when readings after its cutoff change, and score each client against bottom-up on the same scale. Keep the split for a client only when it wins on the decision windows.

## What goes wrong in production {#what-goes-wrong-ch7}

Most failures in this chapter are silent, so they are worth naming before they happen.

The first is a quietly short total. If one client drops out of the sum, the total is smaller than the demand, and its scores still look reasonable. The bottom-up total in this book raises an error when an hour has fewer than thirty client forecasts. The start rule refuses a client with too little history instead of skipping it, as Chapter 6 explains. In production, a run that builds fewer forecasts than clients should stop and name the missing client.

The second is the raw sum. The October repeat hour holds two real hours of energy under one label, so a total built from raw readings can count that hour at roughly twice its neighbours. The result is a demand spike that is not there. The book's total masks the hour instead, and the check in [the first example](https://github.com/rollingedition/book-time-series-forecasting/blob/b681485ba88191f55ea344f70e17416c37cdeea2/examples/total-bottom-up-and-direct.py) excludes the clock-change hours for the same reason.

The third is a split that reads the future. A split whose shares use the window's own readings scores better in a backtest than it will in production. The poisoning check is the test. A share must not move when readings after its cutoff change. The share check in [the second example](https://github.com/rollingedition/book-time-series-forecasting/blob/b681485ba88191f55ea344f70e17416c37cdeea2/examples/total-split-by-share.py) and the scale check in [the first](https://github.com/rollingedition/book-time-series-forecasting/blob/b681485ba88191f55ea344f70e17416c37cdeea2/examples/total-bottom-up-and-direct.py) both return zero, and a production run should keep them as tests that fail loudly.

The fourth is a decision and a report that disagree. The identifier lowers the total's error on the decision windows and raises it on the standard cutoffs. A monitor that watches only one set of windows will miss the other's failure. On every refit, log the total's error with and without the identifier on the same windows, beside the per-client MASE that Chapter 6 uses to decide.

The fifth is a share that goes stale. A share is a fact about the past 8 weeks, so when a client's habits change, its share lags the change for as long as the window is long. A top-down forecast of that client is then wrong in a steady direction, not at random, and the error does not show in the total at all, because the shares still add to one. A monitor should therefore watch each client's share over time, not only the total's error. The per-client MASE in [the second example](https://github.com/rollingedition/book-time-series-forecasting/blob/b681485ba88191f55ea344f70e17416c37cdeea2/examples/total-split-by-share.py) is the measure that sees it.

The sixth is a scale that moves with the window. The total's MASE scale is read once, from the history before the first scored cutoff. A scale refreshed for each window reads that window's own readings, and every score on the total then changes for reasons that have nothing to do with the forecast. [The first example](https://github.com/rollingedition/book-time-series-forecasting/blob/b681485ba88191f55ea344f70e17416c37cdeea2/examples/total-bottom-up-and-direct.py) checks, for each scored cutoff, that the scale for that window does not move when readings from the cutoff on are replaced. The count of comparisons in which it moves is 0 of six.

**Working rule:** In production, check the total against the sum of its readings on every refit, stop when a client is missing from a total, and run the poisoning check on each share and on the scale for each window. Log the total's error with and without the identifier on the same windows. When the windows disagree, report both and do not choose the one that flatters the model.

## Decisions this chapter made {#decisions-ch7}

- **The total is the hourly sum of `ALL30`.** Each client is cut by the start rule before the sum, and an hour is missing when any client's reading in it is masked as a clock-change hour. The sum does not change with the start rule, and the check in the first example shows it.
- **Every forecast hour has a value, and scoring refuses a masked hour.** The output grid is complete through the clock-change hours, and a missing reading is never scored as zero.
- **Both totals are built by hand, in pandas.** The hierarchy has one level, so each route is one sum or one split. `hierarchicalforecast` and MinT are named, and neither is used.
- **The total is forecast bottom-up.** It has the lower MAE on the four decision windows and on the standard cutoffs. The direct total is reported beside it.
- **The direct total's target is unscaled.** On the decision windows it has the lower MAE, so the direct model does not scale its target, unlike the clients' model. The first example prints both settings.
- **The identifier stays in the bottom-up total, as Chapter 6 decided for the clients.** Its cost to the total on the standard cutoffs is reported above, not reversed.
- **The split is not the client method.** Bottom-up has the lower per-client MASE on the decision windows, and on these clients the split loses even with the true total.
- **Shares come from the 1,344 hours before each cutoff, the same history as the clients.** The poisoning check shows that no share reads a later reading.
- **The total's MASE scale is the rule from Chapter 2, applied to the total:** the seasonal naive error over every reading before the first scored cutoff, with clock-change hours masked and the start rule applied to each client first.
- **The windows are Chapter 6's.** The decision windows and the standard cutoffs are the same days, so the two chapters' numbers can be compared line by line.
- **Chapter 8 receives point forecasts:** the bottom-up forecast for each client and for the total, with the direct total as the alternative. A range for the total cannot be built from the clients' ranges.
