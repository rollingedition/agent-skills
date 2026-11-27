---
title: "Glossary"
book: "Time Series Forecasting"
edition: "2026.11.25"
canonical: "https://rollingedition.com/time-series-forecasting/glossary"
---

# Glossary of *Time Series Forecasting*

The 97 terms this book defines, as Edition 2026.11.25 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/time-series-forecasting/glossary

## AICc

The criterion AutoETS uses is AICc, the Akaike information criterion corrected for small samples.

- Also: Akaike information criterion corrected for small samples
- Comes before: AutoETS
- Defined in: [Forecast the next day with one model](forecast-tomorrows-demand.md#forecast-with-a-statistical-model)
- Address: https://rollingedition.com/concepts/data-science/aicc

## alpha

The constant alpha, between 0 and 1, sets how fast the level follows the data.

- Part of: exponential smoothing
- Defined in: [Fit exponential smoothing](fit-statistical-models-per-client.md#fit-exponential-smoothing)
- Address: https://rollingedition.com/concepts/time-series-forecasting/alpha

## ARIMA

An ARIMA model writes the next reading as a weighted sum of earlier readings and earlier errors, after differencing

- Formula: `ARIMA(p,d,q)(P,D,Q)[m]`
- Defined in: [Fit a fixed seasonal ARIMA](fit-statistical-models-per-client.md#fit-a-fixed-seasonal-arima)
- Address: https://rollingedition.com/concepts/time-series-forecasting/arima

## AutoARIMA

AutoARIMA searches for the orders instead of fixing them.

- True for: statsforecast 2.1.1
- Implemented by: statsforecast 2.1.1
- Defined in: [Why the book avoids automatic ARIMA at season 24](fit-statistical-models-per-client.md#why-the-book-avoids-autoarima)
- Address: https://rollingedition.com/concepts/time-series-forecasting/autoarima

## AutoETS

statsforecast 2.1.1 describes AutoETS as selecting the best ETS (error, trend and seasonality) form with an information criterion (statsforecast/models.py, class AutoETS).

- True for: statsforecast 2.1.1
- Implemented by: statsforecast 2.1.1
- Defined in: [Forecast the next day with one model](forecast-tomorrows-demand.md#forecast-with-a-statistical-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/autoets

## average of weeks

Average of weeks takes the mean of the same hour on the same weekday over the four weeks before

- Formula: `forecast(T + k) = (y(T + k - 168) + y(T + k - 336) + y(T + k - 504) + y(T + k - 672)) / 4`
- A kind of: baseline
- Defined in: [Three baselines to beat](beat-the-naive-baselines.md#three-baselines-to-beat)
- Address: https://rollingedition.com/concepts/time-series-forecasting/average-of-weeks

## backtest

a backtest is the score of many windows, each made as it would have been made on its day

- Comes before: leakage
- Defined in: [Why a baseline comes first](beat-the-naive-baselines.md#why-a-baseline-comes-first)
- Address: https://rollingedition.com/concepts/model-evaluation/backtest

## baseline

A baseline is a forecast that needs no fitting.

- Defined in: [Why a baseline comes first](beat-the-naive-baselines.md#why-a-baseline-comes-first)
- Address: https://rollingedition.com/concepts/time-series-forecasting/baseline

## bottom-up

Bottom-up forecasts the bottom level, here the clients, and sums the results.

- Also: bottom-up total
- Contrasts with: top-down
- Computed from: global model
- Defined in: [Why the total needs a check](make-the-total-add-up.md#why-the-total-needs-a-check)
- Address: https://rollingedition.com/concepts/time-series-forecasting/bottom-up

## calendar feature

Calendar features, unlike lags, are facts about the target hour itself: its hour of day, its day of the week and its month.

- Also: calendar features
- A kind of: feature
- Contrasts with: lag
- Defined in: [Add calendar and holiday features](add-calendar-and-lag-features.md#add-calendar-and-holidays)
- Address: https://rollingedition.com/concepts/feature-engineering/calendar-feature

## calibration window

A calibration window is a window whose residuals size the bands.

- Also: calibration windows
- A kind of: window
- Defined in: [Build intervals from residuals](quantify-forecast-uncertainty.md#build-intervals-from-residuals)
- Address: https://rollingedition.com/concepts/time-series-forecasting/calibration-window

## Chronos-2

Chronos-2 is an encoder-only transformer that takes a context of past values and outputs quantiles for the next steps

- A kind of: foundation model
- Defined in: [Load a recorded foundation model's forecasts](compare-prophet-and-a-foundation-model.md#load-a-recorded-foundation-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/chronos-2

## client identifier

A client identifier puts the client in the table as a static categorical feature.

- A kind of: feature
- Defined in: [Identify each client](forecast-many-clients-at-once.md#identify-each-client)
- Address: https://rollingedition.com/concepts/feature-engineering/client-identifier

## coherent

Forecasts that add up are called coherent.

- Also: coherence
- Comes before: bottom-up
- Comes before: top-down
- Comes before: MinT
- Defined in: [Why the total needs a check](make-the-total-add-up.md#why-the-total-needs-a-check)
- Address: https://rollingedition.com/concepts/time-series-forecasting/coherent

## conformal prediction

Conformal prediction builds a band from the residuals of forecasts made the same way on earlier days.

- Computed from: residual
- Computed from: calibration window
- Implemented by: mlforecast 1.1.0
- Implemented by: statsforecast 2.1.1
- Defined in: [Build intervals from residuals](quantify-forecast-uncertainty.md#build-intervals-from-residuals)
- Address: https://rollingedition.com/concepts/data-science/conformal-prediction

## coverage

The share of readings the bounds contain is the coverage

- Measured from: prediction interval
- Defined in: [Why one number is not enough](quantify-forecast-uncertainty.md#why-one-number-is-not-enough)
- Address: https://rollingedition.com/concepts/model-evaluation/coverage

## coverage gap

Barber and co-authors (2023) call the loss in coverage when exchangeability fails a coverage gap.

- Measured from: coverage
- Defined in: [Measure coverage on held-out days](quantify-forecast-uncertainty.md#measure-coverage-on-held-out-days)
- Address: https://rollingedition.com/concepts/model-evaluation/coverage-gap

## critical fractile

The level cu / (cu + co) is the critical fractile of the newsvendor model.

- Formula: `tau = cu / (cu + co)`
- Defined in: [Choose the level from the cost of error](quantify-forecast-uncertainty.md#choose-the-level-from-the-cost-of-error)
- Address: https://rollingedition.com/concepts/data-science/critical-fractile

## cross-learning

Cross-learning, which would let one series inform another, is off by default

- Defined in: [Load a recorded foundation model's forecasts](compare-prophet-and-a-foundation-model.md#load-a-recorded-foundation-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/cross-learning

## cutoff

The moment a forecast is made is its cutoff.

- Part of: window
- Comes before: history
- Defined in: [The case and its data](forecast-tomorrows-demand.md#the-case-and-its-data)
- Address: https://rollingedition.com/concepts/time-series-forecasting/cutoff

## daily MASE

The daily MASE takes each client's mean absolute error over the day's 24 hours, divides it by the client's scale, and averages the results over the thirty clients

- Formula: `daily MASE = mean over clients of (MAE over the day's 24 hours / scale)`
- Computed from: mean absolute scaled error
- Defined in: [Score the log as actuals arrive](keep-the-forecast-running.md#score-the-log-as-actuals-arrive)
- Address: https://rollingedition.com/concepts/model-evaluation/daily-mase

## decision window

Decision windows are the windows the feature set is chosen on, never the standard cutoffs, which are the windows the book reports.

- Also: decision windows
- A kind of: window
- Defined in: [Choose on decision windows](add-calendar-and-lag-features.md#choose-on-decision-windows)
- Address: https://rollingedition.com/concepts/model-evaluation/decision-window

## differencing

differencing: subtracting an earlier reading from each reading, the one immediately before it or the one a season earlier

- Part of: ARIMA
- Defined in: [Fit a fixed seasonal ARIMA](fit-statistical-models-per-client.md#fit-a-fixed-seasonal-arima)
- Address: https://rollingedition.com/concepts/time-series-forecasting/differencing

## direct total

The direct total is one model fitted to the total series itself.

- Contrasts with: bottom-up
- Defined in: [Forecast the total directly](make-the-total-add-up.md#forecast-the-total-directly)
- Address: https://rollingedition.com/concepts/time-series-forecasting/direct-total

## error

The error of an hour is the actual demand minus the forecast.

- Comes before: score
- Defined in: [Score both on a held-out week](forecast-tomorrows-demand.md#score-on-a-held-out-week)
- Address: https://rollingedition.com/concepts/time-series-forecasting/error

## ETS

ETS, for error, trend and season, extends the simplest form of exponential smoothing.

- Comes before: AutoETS
- Defined in: [Fit exponential smoothing](fit-statistical-models-per-client.md#fit-exponential-smoothing)
- Address: https://rollingedition.com/concepts/time-series-forecasting/ets

## exponential smoothing

Exponential smoothing moves its level toward each new reading.

- Formula: `level_t = alpha * y_t + (1 - alpha) * level_(t-1)`
- Comes before: ETS
- Defined in: [Fit exponential smoothing](fit-statistical-models-per-client.md#fit-exponential-smoothing)
- Address: https://rollingedition.com/concepts/time-series-forecasting/exponential-smoothing

## feature

the features: the readings and facts the model may use for the row's hour.

- Also: features
- Part of: feature table
- Close to: https://rollingedition.com/concepts/search-and-recommendation/feature
- Defined in: [Turn history into features](add-calendar-and-lag-features.md#turn-history-into-features)
- Address: https://rollingedition.com/concepts/feature-engineering/feature

## feature table

A feature table has one row for each client and hour that a model learns from or must predict.

- Defined in: [Turn history into features](add-calendar-and-lag-features.md#turn-history-into-features)
- Address: https://rollingedition.com/concepts/feature-engineering/feature-table

## fill

The fill is the mean of the hour before and the hour after, taken from the history before the cutoff only.

- Computed from: history
- Defined in: [Mark clock-change hours as missing](backtest-without-looking-ahead.md#mark-clock-change-hours-as-missing)
- Address: https://rollingedition.com/concepts/time-series-forecasting/fill

## finite-sample levels

Each new residual is one more among n + 1, so the finite-sample levels move outward a little: each quantile level moves to floor((n + 1) * a) / n for the lower bound and ceil((n + 1) * (1 - a)) / n for the upper, where n is the number of residuals and a the tail share.

- Also: finite-sample correction
- Defined in: [Calibrate on earlier windows](quantify-forecast-uncertainty.md#calibrate-on-earlier-windows)
- Address: https://rollingedition.com/concepts/data-science/finite-sample-levels

## flag

A day is flagged when its daily MASE is above twice a reference.

- Computed from: daily MASE
- Defined in: [Flag drift against the backtest](keep-the-forecast-running.md#flag-drift-against-the-backtest)
- Address: https://rollingedition.com/concepts/model-evaluation/flag

## forecast

A forecast here is the expected demand of one client in each hour, made from readings recorded before the forecast was made.

- Part of: window
- Defined in: [The case and its data](forecast-tomorrows-demand.md#the-case-and-its-data)
- Address: https://rollingedition.com/concepts/time-series-forecasting/forecast

## forecast log

A forecast log is a table with one row for each client and hour.

- Defined in: [Log every forecast before its actuals arrive](keep-the-forecast-running.md#log-every-forecast-before-actuals)
- Address: https://rollingedition.com/concepts/time-series-forecasting/forecast-log

## forecast row

Forecast rows are the 24 hours after the cutoff, with features but no target.

- Also: forecast rows
- Part of: feature table
- Defined in: [Turn history into features](add-calendar-and-lag-features.md#turn-history-into-features)
- Address: https://rollingedition.com/concepts/feature-engineering/forecast-row

## forward fill

Forward fill repeats the last reading that arrived.

- Defined in: [Score the log as actuals arrive](keep-the-forecast-running.md#score-the-log-as-actuals-arrive)
- Address: https://rollingedition.com/concepts/data-science/forward-fill

## foundation model

A foundation model is trained once on many series and then applied to a context, here with no fitting on that series.

- Defined in: [Load a recorded foundation model's forecasts](compare-prophet-and-a-foundation-model.md#load-a-recorded-foundation-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/foundation-model

## gap hour

clock_change_gap is 01:00 on a March clock-change day.

- Also: clock_change_gap
- Defined in: [Load one client's hourly demand](forecast-tomorrows-demand.md#load-one-clients-demand)
- Address: https://rollingedition.com/concepts/time-series-forecasting/gap-hour

## global model

A global model fits one set of parameters to many series in a single pass, so every client contributes to what it learns.

- Also: global models, global method, global methods
- Contrasts with: local method
- Contrasts with: per-client model
- Defined in: [One model for many clients](forecast-many-clients-at-once.md#one-model-for-many-clients)
- Address: https://rollingedition.com/concepts/time-series-forecasting/global-model

## history

the history is every reading before the cutoff, all that a forecast may use, though the book's models fit on its last eight weeks

- Defined in: [Why a baseline comes first](beat-the-naive-baselines.md#why-a-baseline-comes-first)
- Address: https://rollingedition.com/concepts/time-series-forecasting/history

## history half

The history half compares each feature on the rows of the eight weeks before each of the three evaluation cutoffs

- Part of: shift test
- Contrasts with: target half
- Defined in: [Check a backtest for leakage](backtest-without-looking-ahead.md#check-a-backtest-for-leakage)
- Address: https://rollingedition.com/concepts/model-evaluation/history-half

## holiday table

Prophet takes holidays as a table of names and dates and fits an effect for each

- True for: prophet 1.5.0
- Part of: Prophet
- Defined in: [Where Prophet fits](compare-prophet-and-a-foundation-model.md#where-prophet-fits)
- Address: https://rollingedition.com/concepts/time-series-forecasting/holiday-table

## horizon

A forecast uses only the readings before its cutoff, and it reaches forward a fixed number of hours, its horizon.

- Part of: window
- Defined in: [The case and its data](forecast-tomorrows-demand.md#the-case-and-its-data)
- Address: https://rollingedition.com/concepts/time-series-forecasting/horizon

## interval score

The interval score adds a band's width to a penalty for each reading that misses the band, the penalty growing with the distance of the miss and scaled by 2 over the miss rate the level allows

- Measured from: prediction interval
- Defined in: [Calibrate on earlier windows](quantify-forecast-uncertainty.md#calibrate-on-earlier-windows)
- Address: https://rollingedition.com/concepts/model-evaluation/interval-score

## lag

The lag of k hours for the hour t is the reading at t minus k.

- Also: lags, lag feature
- A kind of: feature
- Defined in: [Add lags the forecast can see](add-calendar-and-lag-features.md#add-lags-the-forecast-can-see)
- Address: https://rollingedition.com/concepts/feature-engineering/lag

## late starter

A late starter is a client whose first reading falls after the data begins, and so can fall inside the history its model reads.

- Comes before: start rule
- Defined in: [Meet the late starters](fit-statistical-models-per-client.md#meet-the-late-starters)
- Address: https://rollingedition.com/concepts/time-series-forecasting/late-starter

## leakage

A backtest leaks when a window's model sees a reading from at or after its cutoff.

- Also: leak
- Defined in: [Keep the future out of the history](backtest-without-looking-ahead.md#keep-the-future-out-of-history)
- Address: https://rollingedition.com/concepts/model-evaluation/leakage

## level

The level of a series is its typical reading

- Part of: time series
- Defined in: [Why a statistical model comes next](fit-statistical-models-per-client.md#why-a-statistical-model-comes-next)
- Address: https://rollingedition.com/concepts/time-series-forecasting/level

## level

A prediction interval's level, such as 80 or 95, is the share of readings the bounds should contain.

- Part of: prediction interval
- Defined in: [Why one number is not enough](quantify-forecast-uncertainty.md#why-one-number-is-not-enough)
- Address: https://rollingedition.com/concepts/model-evaluation/level

## local method

local methods, which fit each series on its own

- Also: local methods
- Defined in: [One model for many clients](forecast-many-clients-at-once.md#one-model-for-many-clients)
- Address: https://rollingedition.com/concepts/time-series-forecasting/local-method

## LocalStandardScaler

mlforecast's LocalStandardScaler (mlforecast/target_transforms.py), which subtracts the client's mean and divides by its standard deviation.

- True for: mlforecast 1.1.0
- Implemented by: mlforecast 1.1.0
- Defined in: [Measure what each feature adds](add-calendar-and-lag-features.md#measure-what-each-feature-adds)
- Address: https://rollingedition.com/concepts/feature-engineering/local-standard-scaler

## long format

The data is held in long format: one row per client and hour, with three columns.

- Defined in: [One model for many clients](forecast-many-clients-at-once.md#one-model-for-many-clients)
- Address: https://rollingedition.com/concepts/data-science/long-format

## masked reading

A masked reading is neither zero nor a copy; it is missing.

- Defined in: [Take the MASE scale from history](beat-the-naive-baselines.md#take-the-mase-scale-from-history)
- Address: https://rollingedition.com/concepts/data-science/masked-reading

## maximum a posteriori estimate

By default Prophet's fit is a maximum a posteriori estimate, an optimisation rather than a set of sampled draws.

- True for: prophet 1.5.0
- Defined in: [Where Prophet fits](compare-prophet-and-a-foundation-model.md#where-prophet-fits)
- Address: https://rollingedition.com/concepts/data-science/maximum-a-posteriori-estimate

## mean absolute error

The mean absolute error, MAE, is the average size of the miss

- Also: MAE
- Formula: `MAE = mean(abs(actual - forecast))`
- A kind of: score
- Computed from: error
- Implemented by: utilsforecast 0.2.17
- Defined in: [Score both on a held-out week](forecast-tomorrows-demand.md#score-on-a-held-out-week)
- Address: https://rollingedition.com/concepts/model-evaluation/mae

## mean absolute scaled error

MASE, the mean absolute scaled error, is the mean of the absolute scaled errors.

- Also: MASE
- Formula: `MASE = mean of |actual(t) - forecast(t)| / scale`
- Computed from: scaled error
- Implemented by: utilsforecast 0.2.17
- Defined in: [Scale errors with MASE](beat-the-naive-baselines.md#scale-errors-with-mase)
- Address: https://rollingedition.com/concepts/model-evaluation/mase

## mean per-client MASE

The mean per-client MASE is MASE for each client, averaged over the clients, here the eight clients.

- Computed from: mean absolute scaled error
- Defined in: [Measure what each feature adds](add-calendar-and-lag-features.md#measure-what-each-feature-adds)
- Address: https://rollingedition.com/concepts/model-evaluation/mean-per-client-mase

## MinT

MinT chooses the coherent forecasts that minimise the mean squared error of the coherent forecasts, under an unbiasedness assumption

- Defined in: [Why the total needs a check](make-the-total-add-up.md#why-the-total-needs-a-check)
- Address: https://rollingedition.com/concepts/time-series-forecasting/mint

## model string

The model string sets which forms the model may take, with one letter each for error, trend and season.

- True for: statsforecast 2.1.1
- Part of: AutoETS
- Defined in: [Forecast the next day with one model](forecast-tomorrows-demand.md#forecast-with-a-statistical-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/model-string

## monitoring system

A monitoring system covers alerts, dashboards, data quality across many feeds and the people who respond.

- Contrasts with: forecast log
- Contrasts with: flag
- Contrasts with: coverage
- Defined in: [Know when to retire a model](keep-the-forecast-running.md#know-when-to-retire-a-model)
- Address: https://rollingedition.com/concepts/data-science/monitoring-system

## naive

Naive repeats the last reading before the cutoff

- Formula: `forecast(T + k) = y(T - 1)`
- A kind of: baseline
- Implemented by: statsforecast 2.1.1
- Defined in: [Three baselines to beat](beat-the-naive-baselines.md#three-baselines-to-beat)
- Address: https://rollingedition.com/concepts/time-series-forecasting/naive

## NHITS

NHITS is a neural forecaster from the neuralforecast library, which packages neural forecasters for panels of series.

- Defined in: [Why the neural model is recorded](compare-prophet-and-a-foundation-model.md#why-this-edition-has-no-neural-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/nhits

## one-step naive error

The 2006 paper scales by the one-step naive error: the mean absolute difference between each reading and the one before it.

- Also: one-step scale
- Defined in: [Scale errors with MASE](beat-the-naive-baselines.md#scale-errors-with-mase)
- Address: https://rollingedition.com/concepts/model-evaluation/one-step-naive-error

## oracle check

A check this chapter calls the oracle check applies the shares to the actual total, which no forecast can know

- Computed from: share
- Defined in: [Split a total by share](make-the-total-add-up.md#split-a-total-by-share)
- Address: https://rollingedition.com/concepts/model-evaluation/oracle-check

## per-client model

A per-client model is one fit for each client, on that client's history alone, so the cost is one fit per client per window.

- Defined in: [Why a statistical model comes next](fit-statistical-models-per-client.md#why-a-statistical-model-comes-next)
- Address: https://rollingedition.com/concepts/time-series-forecasting/per-client-model

## poisoning check

The poisoning check writes wrong values over every reading from a cutoff on, then confirms that the shares, the total's MASE scale and the start-rule history do not move.

- Defined in: [What goes wrong in production](keep-the-forecast-running.md#what-goes-wrong-ch10)
- Address: https://rollingedition.com/concepts/model-evaluation/poisoning-check

## pooled MAE

The pooled MAE is the MAE over every client-hour in the windows, the single number for the whole supplier.

- Contrasts with: mean per-client MASE
- Defined in: [Measure what each feature adds](add-calendar-and-lag-features.md#measure-what-each-feature-adds)
- Address: https://rollingedition.com/concepts/model-evaluation/pooled-mae

## prediction interval

A prediction interval gives a lower and an upper bound for each hour.

- Also: band
- Defined in: [Why one number is not enough](quantify-forecast-uncertainty.md#why-one-number-is-not-enough)
- Address: https://rollingedition.com/concepts/data-science/prediction-interval

## Prophet

Prophet writes a series as a trend, plus Fourier seasonal terms, plus holiday effects, plus an error term.

- True for: prophet 1.5.0
- Implemented by: prophet 1.5.0
- Defined in: [Where Prophet fits](compare-prophet-and-a-foundation-model.md#where-prophet-fits)
- Address: https://rollingedition.com/concepts/time-series-forecasting/prophet

## quantile loss

The quantile loss is tau * (y - q) when the reading y is at or above the purchase q, and (1 - tau) * (q - y) when it is below.

- Also: pinball loss
- Defined in: [Choose the level from the cost of error](quantify-forecast-uncertainty.md#choose-the-level-from-the-cost-of-error)
- Address: https://rollingedition.com/concepts/model-evaluation/quantile-loss

## rebuilt log

A rebuilt log is leakage in disguise, because it knows what the forecast should have been.

- A kind of: leakage
- Contrasts with: forecast log
- Defined in: [Log every forecast before its actuals arrive](keep-the-forecast-running.md#log-every-forecast-before-actuals)
- Address: https://rollingedition.com/concepts/time-series-forecasting/rebuilt-log

## recursive prediction

In recursive prediction, for a 24-hour horizon, MLForecast forecasts one hour, writes that forecast back as that hour's reading, and repeats for the next hour (_predict_recursive in mlforecast/core.py).

- True for: mlforecast 1.1.0
- Implemented by: mlforecast 1.1.0
- Defined in: [Catch a lag that leaks the future](add-calendar-and-lag-features.md#catch-a-lag-that-leaks)
- Address: https://rollingedition.com/concepts/time-series-forecasting/recursive-prediction

## refit

A refit re-estimates the model's parameters on the history known at a cutoff.

- Defined in: [Refit on a schedule](keep-the-forecast-running.md#refit-on-a-schedule)
- Address: https://rollingedition.com/concepts/time-series-forecasting/refit

## repeat hour

clock_change_repeat is 01:00 on an October clock-change day.

- Also: clock_change_repeat
- Contrasts with: gap hour
- Defined in: [Load one client's hourly demand](forecast-tomorrows-demand.md#load-one-clients-demand)
- Address: https://rollingedition.com/concepts/time-series-forecasting/repeat-hour

## residual

Here a residual is the error of an earlier forecast: the reading minus the forecast, e = y - f.

- Formula: `e = y - f`
- Comes before: conformal prediction
- Defined in: [Build intervals from residuals](quantify-forecast-uncertainty.md#build-intervals-from-residuals)
- Address: https://rollingedition.com/concepts/data-science/residual

## retiring a model

Retiring a model means stopping its use and replacing it.

- Also: retire a model
- Contrasts with: refit
- Defined in: [Know when to retire a model](keep-the-forecast-running.md#know-when-to-retire-a-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/retiring-a-model

## root mean squared error

The root mean squared error, RMSE, is RMSE = sqrt(mean((actual - forecast)^2)).

- Also: RMSE
- Formula: `RMSE = sqrt(mean((actual - forecast)^2))`
- A kind of: score
- Computed from: error
- Contrasts with: mean absolute error
- Implemented by: utilsforecast 0.2.17
- Defined in: [Score both on a held-out week](forecast-tomorrows-demand.md#score-on-a-held-out-week)
- Address: https://rollingedition.com/concepts/model-evaluation/rmse

## scaled error

A scaled error divides each error by a scale, the typical error of a simple method on the same client's own history.

- Computed from: error
- Comes before: mean absolute scaled error
- Defined in: [Scale errors with MASE](beat-the-naive-baselines.md#scale-errors-with-mase)
- Address: https://rollingedition.com/concepts/model-evaluation/scaled-error

## score

A score turns the errors of a set of forecasts into one number.

- Defined in: [Score both on a held-out week](forecast-tomorrows-demand.md#score-on-a-held-out-week)
- Address: https://rollingedition.com/concepts/model-evaluation/score

## season

the season is the shape that repeats in each cycle, here the daily shape of the load

- Part of: ETS
- Defined in: [Why a statistical model comes next](fit-statistical-models-per-client.md#why-a-statistical-model-comes-next)
- Address: https://rollingedition.com/concepts/time-series-forecasting/season

## seasonal naive

Seasonal naive says that each future value equals the last observed value from the same season.

- Also: SeasonalNaive
- Formula: `y(t - 24)`
- A kind of: baseline
- Implemented by: statsforecast 2.1.1
- Defined in: [Forecast the next day with seasonal naive](forecast-tomorrows-demand.md#forecast-with-seasonal-naive)
- Address: https://rollingedition.com/concepts/time-series-forecasting/seasonal-naive

## seasonal scale

under the seasonal scale, the denominator is seasonal naive's error on the client's own history

- Formula: `scale = mean of |y(t) - y(t - 24)|`
- Computed from: seasonal naive
- Measured from: history
- Contrasts with: one-step naive error
- Part of: mean absolute scaled error
- Defined in: [Scale errors with MASE](beat-the-naive-baselines.md#scale-errors-with-mase)
- Address: https://rollingedition.com/concepts/model-evaluation/seasonal-scale

## share

A client's share is its readings summed over its own history, the 1,344 hours before the cutoff, divided by the total's readings summed over the same hours.

- Defined in: [Split a total by share](make-the-total-add-up.md#split-a-total-by-share)
- Address: https://rollingedition.com/concepts/time-series-forecasting/share

## shift test

The shift test compares a feature computed from the history cut at the cutoff with the same feature computed from the whole series.

- Defined in: [Check a backtest for leakage](backtest-without-looking-ahead.md#check-a-backtest-for-leakage)
- Address: https://rollingedition.com/concepts/model-evaluation/shift-test

## start rule

The start rule says that a series begins at its first reading.

- Defined in: [Start each series at its first reading](fit-statistical-models-per-client.md#start-each-series-at-its-first-reading)
- Address: https://rollingedition.com/concepts/time-series-forecasting/start-rule

## statistical model

A statistical model describes how each reading follows from the state of a series or from earlier readings, estimates that from the history, and projects it over the horizon.

- Kinds: ETS
- Kinds: ARIMA
- Contrasts with: seasonal naive
- Defined in: [Why a statistical model comes next](fit-statistical-models-per-client.md#why-a-statistical-model-comes-next)
- Address: https://rollingedition.com/concepts/time-series-forecasting/statistical-model

## step back operator

B the step back operator, so that B y_t is y_(t-1)

- Defined in: [Fit a fixed seasonal ARIMA](fit-statistical-models-per-client.md#fit-a-fixed-seasonal-arima)
- Address: https://rollingedition.com/concepts/time-series-forecasting/step-back-operator

## sustained drift

The first retirement trigger is sustained drift: flags on consecutive days with no calendar cause.

- Measured from: flag
- Defined in: [Know when to retire a model](keep-the-forecast-running.md#know-when-to-retire-a-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/sustained-drift

## target

Each row of a feature table holds the value to predict, which the book calls the target

- Part of: feature table
- Close to: https://rollingedition.com/concepts/natural-language-processing/target
- Defined in: [Turn history into features](add-calendar-and-lag-features.md#turn-history-into-features)
- Address: https://rollingedition.com/concepts/feature-engineering/target

## target half

The target half compares the 24 hours that each cutoff forecasts, computed from the readings before the cutoff only.

- Part of: shift test
- Defined in: [Check a backtest for leakage](backtest-without-looking-ahead.md#check-a-backtest-for-leakage)
- Address: https://rollingedition.com/concepts/model-evaluation/target-half

## time series

A time series is a sequence of readings in time order.

- Defined in: [Load one client's hourly demand](forecast-tomorrows-demand.md#load-one-clients-demand)
- Address: https://rollingedition.com/concepts/time-series-forecasting/time-series

## top-down

Top-down forecasts the top, the total, and splits it down by proportions.

- Also: top-down split
- Computed from: direct total
- Computed from: share
- Defined in: [Why the total needs a check](make-the-total-add-up.md#why-the-total-needs-a-check)
- Address: https://rollingedition.com/concepts/time-series-forecasting/top-down

## trailing mean

a trailing mean: the average of the 24 hours up to and including each hour, which reads nothing after its hour

- A kind of: feature
- Defined in: [Check a backtest for leakage](backtest-without-looking-ahead.md#check-a-backtest-for-leakage)
- Address: https://rollingedition.com/concepts/feature-engineering/trailing-mean

## training row

Training rows are the hours of the history before the cutoff, each with its own features and its own reading as the target.

- Also: training rows
- Part of: feature table
- Contrasts with: forecast row
- Defined in: [Turn history into features](add-calendar-and-lag-features.md#turn-history-into-features)
- Address: https://rollingedition.com/concepts/feature-engineering/training-row

## trend

the trend is the slow drift of the level

- Part of: ETS
- Defined in: [Why a statistical model comes next](fit-statistical-models-per-client.md#why-a-statistical-model-comes-next)
- Address: https://rollingedition.com/concepts/time-series-forecasting/trend

## uncovered band

The second retirement trigger is an uncovered band: the 80% band covers well under 80% of readings on several days.

- Measured from: coverage
- Defined in: [Know when to retire a model](keep-the-forecast-running.md#know-when-to-retire-a-model)
- Address: https://rollingedition.com/concepts/time-series-forecasting/uncovered-band

## window

A window is one cutoff with its horizon and the forecast it produces.

- Part of: backtest
- Defined in: [The case and its data](forecast-tomorrows-demand.md#the-case-and-its-data)
- Address: https://rollingedition.com/concepts/time-series-forecasting/window
