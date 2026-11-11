---
title: "Time Series Forecasting"
chapter: "Compare Prophet and a foundation model"
chapter_id: compare-prophet-and-a-foundation-model
book: time-series-forecasting
edition: 2026.11.1
verified: 2026-11-11
edition_code: HK8M-ENSS
canonical: https://rollingedition.com/time-series-forecasting/compare-prophet-and-a-foundation-model
license: CC BY 4.0
attribution: "“Compare Prophet and a foundation model,” chapter 9 of Time Series Forecasting, Edition 2026.11.1, examples passed Nov 11, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting/compare-prophet-and-a-foundation-model. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Compare Prophet and a foundation model

By the end of this chapter you can fit Prophet on the book's three standard cutoffs, load a recorded foundation model (Chronos-2) and a recorded neural model (NHITS), and score all of them on the same MASE scale against the same readings.

Readers meet Prophet and neural forecasting models outside this book, each with its own claims. The supplier needs something narrower from any model: a day-ahead forecast for each client, and a range it can buy against. Chapter 8 calibrated such ranges on earlier windows. The ranges here are not calibrated that way, so this chapter checks their coverage and does not fix it. So this chapter asks what each model does on the case, on the standard cutoffs, Dec 29 to 31, 2014. Every model is scored against seasonal naive from [Chapter 2](#three-baselines-to-beat) and the global model from [Chapter 6](#one-model-for-many-clients), on the same hours and one MASE scale.

Two of the models are neural, and both are recorded rather than run. Chronos-2 is a foundation model. NHITS is a neural network trained on each cutoff's own history. Chronos-2's pretraining data includes this electricity dataset, so its lead here is an upper bound on what to expect on readings it has not seen.

## Where Prophet fits {#where-prophet-fits}

Prophet is the first model a reader tries beyond the baselines, so we test it first, and its assumptions decide where it can help.

Prophet writes a series as a trend, plus Fourier seasonal terms, plus holiday effects, plus an error term. The authors describe it as "a modular regression model with interpretable parameters that can be intuitively adjusted by analysts" ([Taylor and Letham (2018)](https://doi.org/10.7287/peerj.preprints.3190v2)). By default the fit is a maximum a posteriori estimate, an optimisation rather than a set of sampled draws. The code of version 1.5.0 sets that default in its optimisation call (`models.py`, lines 165 and 172), and its `mcmc_samples` argument defaults to 0 (`forecaster.py`, line 144). Both are in the [Prophet source distribution for the pinned version](https://files.pythonhosted.org/packages/e3/5b/8f9e2387cefc8fab4071f9ece67d89793f3c13566d6349dd43e9d8a5a3e3/prophet-1.5.0.tar.gz). Each client gets its own fit, so Prophet does not learn from the other clients.

Prophet does several things well. It needs no interpolation of missing observations: the code drops rows whose `y` is missing before the fit (`forecaster.py`, line 1335). The clock-change hours are missing in the history by [the rule in Chapter 3](#mark-clock-change-hours-as-missing), so Prophet leaves them out without any extra code. It takes holidays as a table of dates and effects, and the table this chapter tests holds the Portuguese national holidays for 2013 and 2014. The authors report that, on their own series with default settings, Prophet had lower error than auto.arima, ETS, seasonal naive and TBATS ([Taylor and Letham (2018)](https://doi.org/10.7287/peerj.preprints.3190v2)). That result rests on their data, so we cite it as the authors' result and do not use it as evidence about this case.

Several defaults get in the way here. Yearly seasonality turns on only with at least 730 days of history (`forecaster.py`, line 1187), so it stays off with eight weeks. The default interval is 80%, not 95% (`forecaster.py`, line 145). It covers trend uncertainty and observation noise, not the seasonal pattern, unless the model is fitted with full sampling ([Prophet documentation](https://meta.github.io/prophet/docs/uncertainty_intervals.html)). Its coverage therefore makes a narrower claim than the word "interval" suggests. Prophet also assumes that the future trend changes as often, and by as much, as it did in the history ([Prophet documentation](https://meta.github.io/prophet/docs/uncertainty_intervals.html)). With eight weeks of history there is little to learn trend changes from, so in our reading that assumption carries most of the forecast.

**Working rule:** Use Prophet per client when a reader needs its trend and seasonal settings as parameters they can read, and when its scored forecasts beat seasonal naive on the decision windows you chose before scoring. Set its interval width in code, and read its default 80% interval as an 80% interval, never as a 95% range. Check its coverage against the level it claims.

## Run Prophet on the same cutoffs {#run-prophet-on-the-same-cutoffs}

The last section named Prophet's assumptions. This one fixes its settings and runs it on the same hours as every other model.

The comparison uses the three standard cutoffs, at 00:00 on Dec 29, Dec 30 and Dec 31, 2014. These are the windows [Chapters 4 to 8](#meet-the-late-starters) score. Each window's history is the 1,344 hours, eight weeks, before its cutoff, with the start rule applied, so a late starter's history begins at its first reading. Prophet is fitted once for each client and cutoff, so the example makes 90 fits. SUBSET8 is the eight clients that are every fourth of the thirty, starting with the second.

We chose the holiday table on decision windows, not on the standard cutoffs. The ordinary decision windows hold no holiday in their scored hours, so they cannot test a holiday table at all. The holiday decision windows can, so the choice uses both kinds.

Example `prophet-holiday-decision` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · prophet 1.5.0 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Prophet with and without the Portuguese holiday table, on the holiday decision windows for SUBSET8 (B-9, B-10): the
four ordinary decision cutoffs and the seven 2014 holidays before Dec 25, before any standard cutoff is scored. Each
variant is scored on the book's MASE scale beside seasonal naive, on the same hours. The table is kept only if it lowers
the mean per-client MASE; a tie keeps the simpler model. The book's Prophet runs take that setting
(lib.compare.PROPHET_HOLIDAYS)."""
from lib.compare import prophet_windows, seasonal_naive, score
from lib.electricity import load
from lib.features import is_holiday
from lib.panel import DECISION_CUTOFFS, HOLIDAY_DECISION_CUTOFFS
from lib.quirks import mask_clock_changes
from lib.settings import SUBSET8, show

DECISION = sorted([*DECISION_CUTOFFS, *HOLIDAY_DECISION_CUTOFFS])
raw = load(SUBSET8)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
keys = ["unique_id", "ds"]
with_holidays = prophet_windows(df, DECISION, use_holidays=True, workers=2)[keys + ["Prophet"]].rename(
    columns={"Prophet": "WithHolidays"})
without = prophet_windows(df, DECISION, use_holidays=False, workers=2)[keys + ["Prophet"]].rename(
    columns={"Prophet": "NoHolidays"})
forecasts = with_holidays.merge(without, on=keys, validate="one_to_one").merge(
    seasonal_naive(df, DECISION), on=keys, validate="one_to_one")
models = ["WithHolidays", "NoHolidays", "SeasonalNaive"]
per_client, scored = score(raw, forecasts, models, SUBSET8, DECISION)

show("decision windows", len(DECISION))
show("holiday decision windows", len(HOLIDAY_DECISION_CUTOFFS))
show("clients", len(SUBSET8))
show("scored hours", len(scored))
show("holiday hours in the decision windows", int(is_holiday(scored["ds"]).sum()))
for model in models:
    show(f"mean MASE {model}", per_client[model].mean(), digits=3)
show("hours where the forecasts differ", int((scored["WithHolidays"] != scored["NoHolidays"]).sum()))
show("clients where holidays help", int((per_client["WithHolidays"] < per_client["NoHolidays"]).sum()))
show("holiday table kept", "yes" if per_client["WithHolidays"].mean() < per_client["NoHolidays"].mean() else "no")
```

Output:

```text
decision windows: 11
holiday decision windows: 7
clients: 8
scored hours: 2112
holiday hours in the decision windows: 1344
mean MASE WithHolidays: 1.070
mean MASE NoHolidays: 1.061
mean MASE SeasonalNaive: 0.934
hours where the forecasts differ: 768
clients where holidays help: 2
holiday table kept: no
```

The example fits Prophet with and without the table for SUBSET8, on eleven decision windows. Four are ordinary: Nov 25, Nov 26, Dec 2 and Dec 3, 2014. Seven are holidays: Apr 18, Apr 20, Apr 25, May 1, Jun 10, Aug 15 and Dec 8, 2014. All of them come before the held-out week, and none has Christmas Day in its history. The holiday windows hold 1344 client-hours of holiday, and they are the only place the table can change a forecast. 768 of the 2112 scored hours differ between the two variants. Their mean per-client MASE is 1.070 with the table and 1.061 without it, against 0.934 for seasonal naive. A setting is kept only if it lowers the decision-window MASE, and a tie keeps the simpler model. The example's verdict on keeping the table is no, so the table stays off.

The standard cutoffs tell a different story, which we report without using it to choose. Their histories include Christmas Day, and the holiday windows' histories do not. That is a likely reason for the gap, but we did not test which holiday causes it. With the table on, Prophet's mean per-client MASE on the standard cutoffs would be 1.27, against 1.35 with it off. A team that wants the table should test it on its own decision windows before it scores anything.

Daily and weekly seasonality are on, and yearly is off. These are the choices Prophet makes for itself on eight weeks of hourly data: yearly needs at least 730 days, weekly at least two weeks, and daily at least two days of sub-daily data (`forecaster.py`, lines 1187, 1209 and 1223). We set them explicitly and did not tune them. The interval is 95%, set in code and printed as `Prophet interval level`, so coverage sits beside the recordings' 95% ranges. Prophet draws its interval samples from numpy's global generator, so the code sets the seed (`SEED`) before each predict. The fit itself is deterministic.

Example `prophet-thirty-clients-backtest` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · prophet 1.5.0 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Prophet for each of the thirty clients on the three standard cutoffs, with a 95% interval. Its forecasts are scored on
the book's MASE scale beside seasonal naive and the Chapter 6 global model, on the same windows and the same readings."""
import pandas as pd

from lib.compare import (PROPHET_HOLIDAYS, PROPHET_LEVEL, global_forecasts, prophet_windows, report_range,
                         report_subset, score, seasonal_naive)
from lib.electricity import load
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import report_scores
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = pd.DatetimeIndex(EVAL_CUTOFFS)
forecasts = prophet_windows(df, cutoffs).merge(
    seasonal_naive(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one").merge(
    global_forecasts(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one")
models = ["Prophet", "SeasonalNaive", "Global"]
per_client, scored = score(raw, forecasts, models, ALL30)

show("Prophet interval level", PROPHET_LEVEL)
show("Prophet holiday table", "on" if PROPHET_HOLIDAYS else "off")
show("clients scored", scored["unique_id"].nunique())
show("scored hours", len(scored))
show("clients where Prophet beats seasonal naive", int((per_client["Prophet"] < per_client["SeasonalNaive"]).sum()))
show("clients where Prophet beats the global model", int((per_client["Prophet"] < per_client["Global"]).sum()))
report_scores(scored, per_client, models)
report_subset(per_client, models)
report_range(scored, "Prophet", "ProphetLo", "ProphetHi", PROPHET_LEVEL)
# Sensitivity only, not used to choose: the holiday table on the same cutoffs, which the decision windows did not favour.
on = prophet_windows(df, cutoffs, use_holidays=True, workers=2)[["unique_id", "ds", "Prophet"]].rename(
    columns={"Prophet": "ProphetHolidays"})
per_holiday, _ = score(raw, forecasts.merge(on, on=["unique_id", "ds"], validate="one_to_one"),
                       ["ProphetHolidays"], ALL30)
show("mean MASE Prophet with holidays, not chosen", per_holiday["ProphetHolidays"].mean())
```

Output:

```text
Prophet interval level: 95
Prophet holiday table: off
clients scored: 30
scored hours: 2160
clients where Prophet beats seasonal naive: 9
clients where Prophet beats the global model: 6
MAE Prophet: 182.44
MAE SeasonalNaive: 148.26
MAE Global: 122.81
RMSE Prophet: 764.88
RMSE SeasonalNaive: 780.48
RMSE Global: 678.81
mean MASE Prophet: 1.35
mean MASE SeasonalNaive: 1.18
mean MASE Global: 0.91
mean MASE Prophet SUBSET8: 1.39
mean MASE SeasonalNaive SUBSET8: 1.16
mean MASE Global SUBSET8: 1.03
coverage 95 Prophet: 0.918
interval score 95 Prophet: 932.66
mean MASE Prophet with holidays, not chosen: 1.27
```

Every model is scored on [the book's one MASE scale](#take-the-mase-scale-from-history): the seasonal naive error in sample, over every reading before Dec 29, 2014, with the clock-change hours masked. A MASE below 1 means the model's error on the scored hours is smaller than seasonal naive's in-sample error. Each client has its own scale, so a large client does not outweigh a small one.

Over the thirty clients, Prophet's mean per-client MASE is 1.35. Seasonal naive's is 1.18, and the global model's is 0.91. On the eight clients of SUBSET8, the three means are 1.39, 1.16 and 1.03, all from the same run.

The mean hides the spread. Prophet beats seasonal naive on 9 of the thirty clients, and the global model on 6. Pooled over all 2,160 scored hours, its MAE is 182.44 kWh, against 148.26 for seasonal naive and 122.81 for the global model. Its RMSE is 764.88 kWh, against 780.48 and 678.81. Prophet beats seasonal naive on RMSE, so it makes fewer very large misses, but it loses to seasonal naive on MAE and MASE, and to the global model on every measure. Its 95% interval covers 0.918 of the readings, and its interval score is 932.66. Coverage below 0.95 means the interval is too narrow for its stated level on these hours.

On these cutoffs Prophet has a higher mean MASE than seasonal naive, on average and on most clients. That is a result for these cutoffs and this data, and it is not a claim about Prophet in general.

**Working rule:** Set Prophet's seasonality, holidays and interval width in code before you score it, and choose any of them on decision windows, never on the standard cutoffs. Keep the holiday table only if it lowers the MASE on the holiday decision windows. Compare Prophet with seasonal naive and the global model on the same windows and the same scale, and list the clients it loses. Set the seed before each predict, and check that a second run prints the same lines.

## Load a recorded foundation model's forecasts {#load-a-recorded-foundation-model}

Prophet fits each client from its own eight weeks. A foundation model brings what it learned from other series, and this section shows how the book holds its forecasts.

A foundation model is trained once on many series and then applied to a context, with no fitting on that series. Chronos-2 is one such model. It is an encoder-only transformer that takes a context of past values and outputs quantiles for the next steps ([Ansari et al. (2025)](https://arxiv.org/abs/2510.15821); the earlier Chronos model is described in [Ansari et al. (2024)](https://arxiv.org/abs/2403.07815)). Its weights are published as `amazon/chronos-2` on Hugging Face under the Apache-2.0 licence, not gated ([model card](https://huggingface.co/amazon/chronos-2)).

Its pretraining covers this dataset, which limits how far its score can be read. The Chronos-2 report lists the electricity dataset in its pretraining corpus. Appendix A, Table 6 gives "Electricity", with 370 series in the energy domain ([Ansari et al. (2025)](https://arxiv.org/abs/2510.15821)). Those series match the UCI ElectricityLoadDiagrams20112014 dataset the book reads, and the book's thirty clients are drawn from them. The report notes partial overlap with some GIFT-Eval training portions. For strictly zero-shot results it points to a variant trained only on synthetic data, in its Section 5.4. We have not run that variant. The report does not show which readings of these clients the model saw, so the scores below are upper bounds, not out-of-sample results.

We do not run Chronos-2 in an example. Its forecasts are recorded: the model ran once, outside the examples, on a CPU, with the revision pinned to `29ec3766d36d6f73f0696f85560a422f50e8498c`, and the examples read the saved output. The recording is dated Nov 10, 2026. Examples must run offline and give the same output every time, and a model call does neither. A downloaded model can change, and a reader's machine may not hold the files at all.

The input for each client and cutoff is the 1,344 hours before the cutoff, with the start rule applied. None of the standard windows needs that step. Their histories begin on Nov 3, 2014 or later, after the autumn clock change, and the three late starters had their first readings before Nov 3, 2014. The manifest counts no missing values in the contexts, so the clock-change handling changes no scored number here. The package builds a mask from missing values and scales around them ([chronos-forecasting source](https://files.pythonhosted.org/packages/79/0e/f205d4a1841e3740045c40e9e8caeff584937eb561831144ca7b93a29d49/chronos_forecasting-2.3.2.tar.gz), `chronos2/model.py`, line 398). The 90 contexts went in one batch, with each series kept separate. Cross-learning, which would let one series inform another, is off by default, and the recording does not turn it on (`chronos2/pipeline.py`, line 833). So the Dec 30 context does not inform the Dec 29 forecast.

The output is, for each client, cutoff and hour, five quantiles for the next 24 hours: 0.025, 0.1, 0.5, 0.9 and 0.975. That is 2,160 rows. The manifest lists the SHA-256 of the output and of `inputs.csv.gz`, which keeps the exact context each window was given, along with the package versions and the machine, described only as a 4-vCPU Linux container with no GPU.

Not every requested quantile is trained. The package is trained on 21 levels, from 0.01 to 0.99 ([Ansari et al. (2025)](https://arxiv.org/abs/2510.15821)). The levels 0.1, 0.5 and 0.9 are among them, so they are read directly. The levels 0.025 and 0.975 are not, so the package interpolates each one linearly between the two nearest trained levels: 0.01 and 0.05 for the lower, and 0.95 and 0.99 for the upper. The code is `interpolate_quantiles` in `chronos/utils.py`, called from `predict_quantiles` in `chronos2/pipeline.py` ([chronos-forecasting source](https://files.pythonhosted.org/packages/79/0e/f205d4a1841e3740045c40e9e8caeff584937eb561831144ca7b93a29d49/chronos_forecasting-2.3.2.tar.gz)). The manifest names the interpolated levels, and a 95% range built from them is partly the package's interpolation.

Example `recorded-chronos2-check` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · prophet 1.5.0 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Check the recorded Chronos-2 outputs before any score reads them: each file's SHA-256 against manifest.json, the shape
of the forecast file, and whether any row's quantiles run out of order. The model is not run; the recording is read."""
from lib.compare import check_recording
from lib.settings import show

for label, value in check_recording().items():
    show(label, value)
```

Output:

```text
outputs checked: 2
hash mismatches: 0
rows: 2160
clients: 30
windows: 3
interpolated levels: 2
rows with quantiles out of order: 0
largest quantile crossing, kWh: 0.00
inverted 80 or 95 ranges: 0
```

The check reads each output file, hashes it, and compares the hash with `manifest.json`. It then counts the rows, clients and cutoffs of the forecast file. It prints 2 outputs, with 0 hash mismatches. The file holds 2160 rows for 30 clients and 3 cutoffs. The manifest names 2 interpolated levels, and 0 rows have quantiles out of order. The check verifies the output files, not the prompt hash, which covers the input and the configuration.

The licence decides which weights the book can run or record: this book uses only Apache-2.0 or MIT weights. Chronos-2's weights and the `chronos-forecasting` package are Apache-2.0 ([model card](https://huggingface.co/amazon/chronos-2); [package metadata](https://pypi.org/pypi/chronos-forecasting/2.3.2/json)). Two other families were considered and are not used. The TimesFM 3.0 weights carry a non-commercial licence, which allows non-commercial and non-production use only ([TimesFM 3.0 licence](https://huggingface.co/google/timesfm-3.0-pytorch/blob/main/LICENSE)). TimesFM 2.5 is Apache-2.0 ([TimesFM 2.5 card](https://huggingface.co/google/timesfm-2.5-200m-pytorch)), so the licence depends on the version named. The Moirai R-series checkpoints are tagged CC-BY-NC-4.0, which is also non-commercial ([Moirai 2.0 card](https://huggingface.co/Salesforce/moirai-2.0-R-small)).

A later edition can run Chronos-2 live once its weights and package fit the release service's limits. Until then the recording stands in for the live run.

**Working rule:** Record a foundation model only with its script, its pinned revision, its package versions and a manifest that hashes every output. Read the recorded outputs in every example, and check the hashes before any score reads them. Check the licence of the weights, not only the licence of the package, and name the model version in any licence sentence.

## Score the recordings on the same cutoffs {#score-the-recording-on-the-same-cutoffs}

The recordings mean something only when they are scored on the same hours as Prophet and the baselines.

A forecast with five quantiles can be scored in two ways. The median, the 0.5 quantile, is a point forecast, scored with MASE on the book's scale. The 0.1 and 0.9 quantiles form an 80% range, and the 0.025 and 0.975 quantiles form a 95% range. Each range is scored by coverage, the share of readings inside it, and by the interval score, which adds the width to a penalty for each reading outside it. The penalty is 2 divided by the nominal miss rate, 0.05 for a 95% range, times the distance outside. [Chapter 8](#calibrate-on-earlier-windows) defines the interval score with its source. Each quantile is also scored by its quantile loss, which charges tau for each kWh a reading falls above the quantile and one minus tau for each kWh below it ([Chapter 8](#choose-the-level-from-the-cost-of-error)).

The scoring runs on the same thirty clients, cutoffs, 2,160 hours and MASE scale as [the Prophet run](#run-prophet-on-the-same-cutoffs). The global model and seasonal naive are rebuilt in each example, not copied from Chapter 6, so every model goes through one scoring path.

Example `recorded-chronos2-score` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · prophet 1.5.0 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Score the recorded Chronos-2 forecasts on the same three standard cutoffs and MASE scale as the other models. The median
is the point forecast. The 80% range runs from the 0.1 to the 0.9 quantile, and the 95% range from 0.025 to 0.975.
The code reads the recording only; it never calls the model."""
import pandas as pd

from lib.compare import (global_forecasts, recorded_forecasts, report_pinball, report_range, report_subset, score,
                         seasonal_naive)
from lib.electricity import load
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import report_scores
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = pd.DatetimeIndex(EVAL_CUTOFFS)
forecasts = recorded_forecasts().merge(
    seasonal_naive(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one").merge(
    global_forecasts(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one")
models = ["Chronos", "SeasonalNaive", "Global"]
per_client, scored = score(raw, forecasts, models, ALL30)

show("clients scored", scored["unique_id"].nunique())
show("scored hours", len(scored))
show("clients where Chronos beats seasonal naive", int((per_client["Chronos"] < per_client["SeasonalNaive"]).sum()))
report_scores(scored, per_client, models)
report_subset(per_client, models)
report_pinball(scored, "Chronos", "q10", 0.1)
report_pinball(scored, "Chronos", "q50", 0.5)
report_pinball(scored, "Chronos", "q90", 0.9)
report_range(scored, "Chronos", "q10", "q90", 80)
report_range(scored, "Chronos", "q025", "q975", 95)
```

Output:

```text
clients scored: 30
scored hours: 2160
clients where Chronos beats seasonal naive: 27
MAE Chronos: 100.13
MAE SeasonalNaive: 148.26
MAE Global: 122.81
RMSE Chronos: 655.39
RMSE SeasonalNaive: 780.48
RMSE Global: 678.81
mean MASE Chronos: 0.81
mean MASE SeasonalNaive: 1.18
mean MASE Global: 0.91
mean MASE Chronos SUBSET8: 0.87
mean MASE SeasonalNaive SUBSET8: 1.16
mean MASE Global SUBSET8: 1.03
quantile loss 0.1 Chronos: 39.44
quantile loss 0.5 Chronos: 50.07
quantile loss 0.9 Chronos: 17.85
coverage 80 Chronos: 0.749
interval score 80 Chronos: 572.89
coverage 95 Chronos: 0.944
interval score 95 Chronos: 958.19
```

Example `recorded-nhits-score` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · prophet 1.5.0 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Score the recorded NHITS forecasts on the same three cutoffs and MASE scale as Chronos-2 and the other models. The
median is the point forecast. The 80% range runs from the 0.1 to the 0.9 quantile, and the 95% range from 0.025 to
0.975. Each level is trained directly by MQLoss, so no range is interpolated. The code reads the recording only."""
import pandas as pd

from lib.compare import (global_forecasts, recorded_forecasts, report_pinball, report_range, report_subset, score,
                         seasonal_naive)
from lib.electricity import load
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.scoring import report_scores
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = pd.DatetimeIndex(EVAL_CUTOFFS)
forecasts = recorded_forecasts("nhits", "NHITS").merge(
    seasonal_naive(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one").merge(
    global_forecasts(df, cutoffs), on=["unique_id", "ds"], validate="one_to_one")
models = ["NHITS", "SeasonalNaive", "Global"]
per_client, scored = score(raw, forecasts, models, ALL30)

show("clients scored", scored["unique_id"].nunique())
show("scored hours", len(scored))
show("clients where NHITS beats seasonal naive", int((per_client["NHITS"] < per_client["SeasonalNaive"]).sum()))
report_scores(scored, per_client, models)
report_subset(per_client, models)
report_pinball(scored, "NHITS", "q10", 0.1)
report_pinball(scored, "NHITS", "q50", 0.5)
report_pinball(scored, "NHITS", "q90", 0.9)
report_range(scored, "NHITS", "q10", "q90", 80)
report_range(scored, "NHITS", "q025", "q975", 95)
```

Output:

```text
clients scored: 30
scored hours: 2160
clients where NHITS beats seasonal naive: 24
MAE NHITS: 136.61
MAE SeasonalNaive: 148.26
MAE Global: 122.81
RMSE NHITS: 649.41
RMSE SeasonalNaive: 780.48
RMSE Global: 678.81
mean MASE NHITS: 1.03
mean MASE SeasonalNaive: 1.18
mean MASE Global: 0.91
mean MASE NHITS SUBSET8: 1.17
mean MASE SeasonalNaive SUBSET8: 1.16
mean MASE Global SUBSET8: 1.03
quantile loss 0.1 NHITS: 27.66
quantile loss 0.5 NHITS: 68.31
quantile loss 0.9 NHITS: 40.58
coverage 80 NHITS: 0.700
interval score 80 NHITS: 682.37
coverage 95 NHITS: 0.877
interval score 95 NHITS: 1250.94
```

| Model | Mean MASE, ALL30 | Mean MASE, SUBSET8 | MAE, ALL30 (kWh) |
| --- | --- | --- | --- |
| Seasonal naive | 1.18 | 1.16 | 148.26 |
| Global model (Chapter 6) | 0.91 | 1.03 | 122.81 |
| Chronos-2, median | 0.81 | 0.87 | 100.13 |
| NHITS, median | 1.03 | 1.17 | 136.61 |
| Prophet, point forecast | 1.35 | 1.39 | 182.44 |

On the median, Chronos-2 has a mean per-client MASE of 0.81 across the thirty clients, and 0.87 on SUBSET8. It has the lowest mean of the five models on both sets, and it beats seasonal naive on 27 of the thirty clients. The global model from Chapter 6 is second on both sets. [Chapter 4's fixed seasonal ARIMA](#fit-a-fixed-seasonal-arima), on the same eight clients, cutoffs and scale, scores 1.09 on SUBSET8, between the global model and seasonal naive. NHITS is third on the thirty clients, at 1.03, and fourth on SUBSET8, at 1.17, narrowly behind seasonal naive's 1.16. Prophet has the highest mean on both sets.

The lead needs its caveat. Chronos-2's pretraining corpus includes this dataset ([the recording section](#load-a-recorded-foundation-model)), so these readings may have been part of its training. Its score here is an upper bound on what to expect on readings it has not seen. NHITS has no such advantage, because each of its cutoffs was trained only on that cutoff's own context. NHITS trails Chronos-2 on the same hours, but the two are not on equal footing, and this chapter does not rank them on this comparison.

The median is also a check on the quantile arithmetic. The pinball loss at 0.5 is half the absolute error, so it should equal half the median's MAE. For Chronos-2 the loss at 0.1 is 39.44, at 0.5 it is 50.07, and at 0.9 it is 17.85. The 0.5 value is the MAE of 100.13 kWh divided by two. For NHITS the losses are 27.66, 68.31 and 40.58, and its 0.5 value is likewise half its MAE of 136.61 kWh.

For the ranges, Chronos-2's 80% range covers 0.749 of the readings, a little under its level of 0.80, and its interval score is 572.89. Its 95% range covers 0.944, close to its level, with an interval score of 958.19. Prophet's 95% range covers 0.918 with an interval score of 932.66. On the interval score Prophet's range is a little lower than Chronos-2's, but its coverage sits further from its level. The Chronos-2 95% range is partly interpolated, so its score is for the model and the package together.

NHITS's ranges are too narrow for their levels on these hours. Its 80% range covers 0.700 of the readings, and its 95% range covers 0.877. Its interval scores are 682.37 at 80% and 1250.94 at 95%, the highest of the three 95% ranges. Its quantiles are trained directly, so no range is interpolated. The recording does not put its quantiles in order, though. The check counts 22 of the 2,160 rows with an adjacent pair out of order, by at most 21.11 kWh. It also counts 0 inverted 80% or 95% ranges. The scores use the values as recorded.

Four limits apply. These are three cutoffs in one week of one dataset, so the results are not a general claim about any model. Neither range was calibrated on the calibration windows that Chapter 8 used, so the coverage here is a check, not a calibration. The Chronos-2 scores are upper bounds, as above, and its 95% range is partly the package's interpolation. The comparison makes no choice. Decisions in this book are made on decision windows, and the recordings have no forecasts there, so nothing is picked with these scores.

**Working rule:** Score a recorded forecast on the same windows, the same scale and the same readings as every other model, and name any interpolated quantile wherever its range is reported. Before you read a lead, check what the model was trained on, because a model that saw the scored readings cannot show skill on them. Do not choose a model or a setting on these windows. A recorded forecast with no forecasts on the decision windows cannot be chosen for production until it has them.

## Why the neural model is recorded {#why-this-edition-has-no-neural-model}

This edition runs no neural model. Its two neural forecasts are recorded, and the reason is the cost of the runtime, not a verdict on neural models.

NHITS is a neural forecaster from the neuralforecast library, which packages neural forecasters for panels of series. The library is Apache-2.0 ([neuralforecast metadata](https://pypi.org/pypi/neuralforecast/3.3.0/json)). We record NHITS the way Chronos-2 is recorded, with its own script, pinned version and manifest, and score it beside Chronos-2 on the same contexts, cutoffs, scale and metrics. Its recording trains once for each cutoff on the same thirty 1,344-hour contexts that Chronos-2 was given. The input window is 168 hours, one week, and the horizon is 24 hours. The five levels are trained directly under the MQLoss loss, with one output for each level. The scaler is neuralforecast's standard scaler, the seed is fixed, and the run is on a CPU. Each cutoff's model sees only that cutoff's context, so no reading after the cutoff reaches it. The weights are not shipped.

Example `recorded-nhits-check` (Python 3.13.16 · holidays 0.108 · lightgbm 4.7.0 · mlforecast 1.1.0 · numpy 2.4.6 · pandas 2.3.3 · prophet 1.5.0 · statsforecast 2.1.1 · utilsforecast 0.2.17), passing in Edition 2026.11.1:

```python
"""Check the recorded NHITS outputs before any score reads them: the file's SHA-256 against manifest.json, the shape of the
forecast file, and whether any row's quantiles run out of order. NHITS is not run; the recording is read."""
from lib.compare import check_recording
from lib.settings import show

for label, value in check_recording("nhits").items():
    show(label, value)
```

Output:

```text
outputs checked: 1
hash mismatches: 0
rows: 2160
clients: 30
windows: 3
interpolated levels: 0
rows with quantiles out of order: 22
largest quantile crossing, kWh: 21.11
inverted 80 or 95 ranges: 0
```

The check reads the NHITS files the way the Chronos-2 check does. It compares each file's hash with the manifest, and it prints the same counts, with zero interpolated levels, because every NHITS level is trained directly.

The reason it is not run live is the runtime. The library brings torch, ray and pytorch-lightning. With them installed, the environment the examples need grows from 687 MB to 1.7 GB. The release service runs every example on 2 vCPU with 4 GiB of memory, and training on a CPU takes longer than an example should take. These two costs decide the matter. It is not a conflict between versions. The NHITS requirements file, `recordings/requirements-nhits.txt`, installs neuralforecast with the same pandas version the examples pin (2.3.3).

Chronos-2 has its own stack. Its requirements file, `recordings/requirements.txt`, installs `chronos-forecasting` with transformers and torch, and it pins pandas 3 for the recording. The package does not need pandas 3. Its metadata accepts pandas from 2.0 up to, but not including, 4 ([chronos-forecasting source](https://files.pythonhosted.org/packages/79/0e/f205d4a1841e3740045c40e9e8caeff584937eb561831144ca7b93a29d49/chronos_forecasting-2.3.2.tar.gz), `pyproject.toml`). The examples never import either package. They read the saved outputs.

A later edition can run NHITS live. That needs a runtime that fits the release service's limits, or a runtime of its own. Either way the windows, the scale and the scoring in this chapter stay the same, so a later model is scored beside the others on the same hours.

**Working rule:** Keep a model out of the examples' runtime when its dependencies would break the runtime budget, and record it instead, with its pins in a separate requirements file. Before you add a dependency, install it in a clean environment and measure what it adds in size and in packages. A resolve that moves a pinned package is a reason to record the model, not a reason to change the pin.

## What goes wrong in production {#what-goes-wrong-ch9}

Prophet's holiday table covers 2013 and 2014 only. The book's runs leave it off, because the holiday decision windows gave no reason to turn it on, but the standard cutoffs show that it moves the result. A forecast made in 2015 with the table unchanged gets no holiday effect on later holidays, and no error is raised. A team that turns the table on must extend it to the forecast's years. Holidays are known in advance, so the fix is to extend the table. Count the holiday hours in each window as well. A window that contains a holiday should show a count above zero, and a count of zero where a holiday falls is the sign to look for.

The interval width is the second failure. A Prophet interval left at its default of 80% gets read as a 95% range by a reader who sees only the word "interval" in a report. The coverage line is the check. Printed beside its level, a coverage near 0.8 is correct for an 80% interval and a failure for a 95% one. Print the level with the coverage every time.

A recorded forecast goes stale in a different way. The recording covers three cutoffs. A day-ahead forecast in production needs one cutoff every day, and the release service does not run the model. Covering another cutoff means running the model, saving its output and hashing it, which is work outside the examples. The sign that the recording is out of date is a window with no rows in the file, which the check's window count shows.

A later model revision changes every number that depends on the recording, even when the code does not change. Treat the revision as an update trigger. Record it, score it on the same windows as the old one, and compare the two before the replacement recording is used. A package that changes its interpolation between versions changes the 95% range without touching the median, so the manifest's list of interpolated levels should be compared as well.

A recorded forecast can also break the order of its own quantiles. The NHITS recording does, by a few kWh in a small number of rows. A range built from a crossed pair would be read as inverted. The check counts the crossings, and a consumer should sort or reject such rows before it uses them.

Prophet's trend assumption fails when a client's demand moves to a different level, as it does after a change of contract or the loss of a large load. Prophet expects the trend to change as often as it did in the history, and its default interval does not cover the seasonal pattern. The sign is residuals that keep one sign across successive windows, and a coverage line that falls over them. The fix is a refit on a shorter history for that client, not a wider interval.

**Working rule:** Before any Prophet or recorded forecast is reported, check that the holiday table covers the forecast's years when the table is on, that the interval level is printed beside its coverage, that the recording has a window for every cutoff in use, that its quantiles are in order, and that the model revision matches the one scored. A failed check stops the report, and the report says which check failed.

## Decisions this chapter made {#decisions-ch9}

- **Prophet runs on all thirty clients, not only on SUBSET8.** Running all thirty puts Prophet beside the global model on the same clients. The SUBSET8 means are printed from the same run.
- **Prophet's interval is 95%, set in code and printed.** Its coverage and interval score then sit beside the recordings' 95% ranges. The default of 80% is not used.
- **Prophet's seasonality flags are fixed in code.** Daily and weekly seasonality are on and yearly is off. These are the choices Prophet makes for eight weeks of hourly data, set explicitly.
- **The holiday table is off.** On the holiday decision windows the table raised the mean MASE, so the simpler model was kept. On the standard cutoffs the table would have lowered Prophet's mean MASE, and we report that figure without using it to choose.
- **Chronos-2 and NHITS are recorded, not run.** The examples read the saved outputs, check their hashes, and never call a model. Examples must run offline and give the same output every time.
- **NHITS is recorded for its runtime cost.** Its dependencies would take the examples' runtime from 687 MB to 1.7 GB, past the release service's 2 vCPU and 4 GiB, and a CPU training run takes longer than an example should.
- **Chronos-2's 95% range is scored with its two interpolated quantiles, and the chapter says so.** NHITS's quantiles are trained directly, so none of its ranges is interpolated.
- **The Chronos-2 lead is read as an upper bound.** Its pretraining corpus includes this dataset, so its score here is not out-of-sample.
- **No model or setting is chosen on the standard cutoffs or the held-out week.** The decision windows are the only place a choice is made. The recordings have no forecasts there, so this chapter makes no choice with them.
