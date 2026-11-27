---
name: time-series-forecasting
description: "Use when forecasting many related hourly or daily series, such as energy demand a day ahead: baselines to beat, leakage-free backtests, MASE scored on history, statistical and gradient-boosting models, totals that add up, conformal intervals and a buy level from costs, Prophet and recorded foundation-model comparisons, and keeping a daily forecast running. When someone explicitly asks to be taught, tutored or quizzed on what this book covers (\"teach me\", \"tutor me\", \"quiz me\"), it also tutors them, one question at a time. Not for a one-off \"explain X\" or \"what is X\"."
license: CC-BY-NC-4.0 AND MIT
compatibility: "The book's examples ran on Python 3.13.16 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Time Series Forecasting"
  edition: "2026.11.26"
  verified: "2026-11-27"
  examples: "56 of 56 examples pass"
  edition-code: "HVW6-R90X"
  source: "https://rollingedition.com/time-series-forecasting"
---

# Time Series Forecasting

This agent skill is *Time Series Forecasting*, Edition 2026.11.26, from Rolling Edition. Examples passed Nov 27, 2026: 56 of 56 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `time-series-forecasting` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Use the book's terms as it defines them.** The book's Glossary has each term it defines, in the book's own sentence, with its section: https://rollingedition.com/time-series-forecasting/glossary. The Rolling Edition MCP server's `define` gives one with its section, its edition and the version it's true for: where the task uses one, it means that.
- **Is this copy current?** Call `check_code` with `HVW6-R90X` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/time-series-forecasting
- **Credit the book** when you quote it or reuse its code: Time Series Forecasting, Edition 2026.11.26, examples passed Nov 27, 2026. By Rolling Edition, https://rollingedition.com/time-series-forecasting. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `time-series-forecasting` plugin and the zip on the book's page at rollingedition.ai.

Terms used below. **Held-out week:** the final seven days of the data, which no choice may read (Dec 25 to 31, 2014 in this book; [Why one test week misleads](https://rollingedition.com/time-series-forecasting/s/why-one-test-week-misleads)). **Scored (standard) cutoffs:** the cutoffs whose forecasts the report publishes, here the last three days at 00:00 ([Score thirty clients on the same cutoffs](https://rollingedition.com/time-series-forecasting/s/score-thirty-clients-on-the-same-cutoffs)). **Decision windows:** earlier cutoffs, before the held-out week, used only to choose ([Compare the two totals](https://rollingedition.com/time-series-forecasting/s/compare-the-two-totals)). **Holiday decision windows:** decision cutoffs on earlier public holidays, used with the ordinary ones to decide a holiday feature or table ([Measure what each feature adds](https://rollingedition.com/time-series-forecasting/s/measure-what-each-feature-adds)).

## Set baselines and score with MASE from history

**When to use:** before comparing any model, and whenever the series differ in size.

1. Implement naive, seasonal naive and, if the series has a weekly rhythm, average of weeks ([Three baselines to beat](https://rollingedition.com/time-series-forecasting/s/three-baselines-to-beat)). Use the library's naive at 2.1.1; write average of weeks in plain code.
2. Check one forecast by hand against its formula ([Three baselines to beat](https://rollingedition.com/time-series-forecasting/s/three-baselines-to-beat)).
3. Score every method on the same windows, histories and code, and count missing forecasts before reading any score ([Why a baseline comes first](https://rollingedition.com/time-series-forecasting/s/why-a-baseline-comes-first)).
4. Build each series' scale once per backtest: the mean absolute difference from the reading one season earlier (lag 24 for hourly data with a daily cycle), over every reading before the first scored cutoff. Mask clock-change readings, drop pairs that touch them, and count a late starter from its first reading. A series with no reading before the first scored cutoff is left out of MASE and reported ([Scale errors with MASE](https://rollingedition.com/time-series-forecasting/s/scale-errors-with-mase), [Score thirty clients on the same cutoffs](https://rollingedition.com/time-series-forecasting/s/score-thirty-clients-on-the-same-cutoffs)).
5. Print the scale's last reading. It must be the hour before the first scored cutoff ([Take the MASE scale from history](https://rollingedition.com/time-series-forecasting/s/take-the-mase-scale-from-history)).
6. Do not name a winner on one window set ([Read a baseline's score](https://rollingedition.com/time-series-forecasting/s/read-a-baselines-score)).

**Check:** the scale's last reading is the hour before the first scored cutoff, every method has the same forecast count, and MASE is printed beside MAE with its history.

**Pitfalls:**
- A scale that reads the scored hours raises no error and looks normal ([Take the MASE scale from history](https://rollingedition.com/time-series-forecasting/s/take-the-mase-scale-from-history)).
- A missing hour shifts a seasonal lag silently ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch2)).

## Backtest without looking ahead

**When to use:** before trusting any score, for every method, including one that reads features.

1. Census the clock changes first: find the time zone and change days, and count what each change hour holds against its neighbours (missing, near zero, or two hours under one label). Check whether timestamps are local time or UTC ([Meet the clock changes](https://rollingedition.com/time-series-forecasting/s/meet-the-clock-changes), [The March hour that reads zero](https://rollingedition.com/time-series-forecasting/s/the-march-hour-that-reads-zero), [The October hour that holds two](https://rollingedition.com/time-series-forecasting/s/the-october-hour-that-holds-two)) with [the example](https://rollingedition.com/time-series-forecasting/s/the-march-hour-that-reads-zero). In this book's data, the March 01:00 label reads zero and the October 01:00 label holds two hours.
2. Prefer a year of cutoffs, including odd days of the week, before trusting a difference between methods. When cost forces fewer, say so beside each score ([Why one test week misleads](https://rollingedition.com/time-series-forecasting/s/why-one-test-week-misleads)).
3. Fix the history length in hours for every window. Slice by cutoff and timestamp, never by row position ([Roll the cutoff forward](https://rollingedition.com/time-series-forecasting/s/roll-the-cutoff-forward), [Keep the future out of the history](https://rollingedition.com/time-series-forecasting/s/keep-the-future-out-of-history)).
4. Mask the change hours your census found, in every history and score ([Mark clock-change hours as missing](https://rollingedition.com/time-series-forecasting/s/mark-clock-change-hours-as-missing)). Do not halve a repeated hour: it holds two hours of energy under one label. Fill a masked hour from history before the cutoff only if the model cannot take gaps. A gap that is not a change hour is an error to stop on, not a value to fill ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch10)).
5. Run the shift test on every feature, at several cutoffs through the year, one on a clock-change day if the feature reads the hour before it. Require zero differing rows ([Check a backtest for leakage](https://rollingedition.com/time-series-forecasting/s/check-a-backtest-for-leakage)) with [the example](https://rollingedition.com/time-series-forecasting/s/check-a-backtest-for-leakage).
6. Log each history's first and last timestamps and its masked-hour count beside the scores ([Keep the future out of the history](https://rollingedition.com/time-series-forecasting/s/keep-the-future-out-of-history), [What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch3)).

**Check:** each history ends an hour before its cutoff, the masked count is the same on every run, and the shift test shows zero differing rows.
**Pitfalls:**
- A history-only check passes a lag of one hour. The target-hour check differs on 69 of 72 target hours ([Check a backtest for leakage](https://rollingedition.com/time-series-forecasting/s/check-a-backtest-for-leakage)).
- Choosing on the scored cutoffs fits the method to the test. Choose on decision windows, and fix the choice before scoring ([Compare the two totals](https://rollingedition.com/time-series-forecasting/s/compare-the-two-totals)).
- A check that cannot fail proves nothing. Run each check once on a deliberately leaky version and confirm it fails ([Log every forecast before its actuals arrive](https://rollingedition.com/time-series-forecasting/s/log-every-forecast-before-actuals), [Split a total by share](https://rollingedition.com/time-series-forecasting/s/split-a-total-by-share)).

## Fit statistical models per series

**When to use:** when each series needs its own model and seasonal form, and the budget allows one fit per series per window.

1. Count fits before choosing windows: series times windows, times refits. Cut series or windows, never scored windows, and write the cut beside the score ([Budget the run time](https://rollingedition.com/time-series-forecasting/s/budget-the-run-time)).
2. Start with automatic exponential smoothing at 2.1.1, season length set to the cycle (24 for hourly data with a daily cycle), and print each series' chosen form ([Fit exponential smoothing](https://rollingedition.com/time-series-forecasting/s/fit-exponential-smoothing)) with [the example](https://rollingedition.com/time-series-forecasting/s/fit-exponential-smoothing).
3. A series that takes a form with no season is suspect ([the flat-form check](https://rollingedition.com/time-series-forecasting/s/fit-exponential-smoothing)). If the seasonal fit has the lower likelihood, force the season with `model="ZZA"`, and score both forms on decision windows before keeping either ([Fit exponential smoothing](https://rollingedition.com/time-series-forecasting/s/fit-exponential-smoothing)) with [the example](https://rollingedition.com/time-series-forecasting/s/fit-exponential-smoothing).
4. When a search is too slow, fix the order in the call and refit it at every cutoff ([Fit a fixed seasonal ARIMA](https://rollingedition.com/time-series-forecasting/s/fit-a-fixed-seasonal-arima)).
5. Score all candidates on the same cutoffs, history and scale, MAE and MASE side by side. Choose on decision windows, never the scored cutoffs, and add windows if models are within about a tenth of MASE ([Compare models on the same cutoffs](https://rollingedition.com/time-series-forecasting/s/compare-models-on-the-same-cutoffs)).

**Check:** forms are printed for every window, and a fixed-order summary lists the intended terms.

**Pitfall:** a season length of 1 gives no error, only forms with no daily pattern ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch4)).

## Start each series at its first reading

**When to use:** whenever a series has leading zeros, as a series that starts inside the history does.

1. Find each series' first non-zero reading from rows before the cutoff only, and cut the history there. Do not fill the zeros before it ([Start each series at its first reading](https://rollingedition.com/time-series-forecasting/s/start-each-series-at-its-first-reading), [A history that starts with zeros](https://rollingedition.com/time-series-forecasting/s/a-history-that-starts-with-zeros)) with [the example](https://rollingedition.com/time-series-forecasting/s/a-history-that-starts-with-zeros).
2. Before trimming, check the rule on the whole series. Count the rows it would drop across all of it, and compare that count with any independent record of start dates, if your data has one. Every dropped row must be zero ([Apply the start rule to every client](https://rollingedition.com/time-series-forecasting/s/apply-the-start-rule-to-every-client)).
3. Refuse a cutoff where a series has no non-zero reading before it, or too little history since its first reading (the book uses 48 hours). Name the series. Never skip it, because a skipped series makes a total quietly short ([Apply the start rule to every client](https://rollingedition.com/time-series-forecasting/s/apply-the-start-rule-to-every-client)).
4. Print the history length at each cutoff.

**Check:** every history length and refused cutoff is printed and explained.

## Build lag and calendar features

**When to use:** when a model reads lagged readings or calendar and holiday flags.

1. Build each feature row as if its window's cutoff were the last reading. A feature for a forecast hour may use only readings at or before that cutoff ([Turn history into features](https://rollingedition.com/time-series-forecasting/s/turn-history-into-features)).
2. Use only lags at least as long as the horizon, so with a 24-hour horizon, 24 hours and longer ([Add lags the forecast can see](https://rollingedition.com/time-series-forecasting/s/add-lags-the-forecast-can-see)).
3. Add calendar and holiday features one set at a time. Use a holiday calendar covering every year in the data and every forecast year, and print the count for each year. Zero means the list lacks that year ([Add calendar and holidays](https://rollingedition.com/time-series-forecasting/s/add-calendar-and-holidays)).
4. Keep a set only when it lowers mean per-series MASE against the set it extends, on decision windows, never on the scored cutoffs. A holiday set is decided on the holiday decision windows together with the ordinary ones. Report pooled MAE beside it ([Measure what each feature adds](https://rollingedition.com/time-series-forecasting/s/measure-what-each-feature-adds)). In this book's data, no holiday feature was kept.
5. Run the shift test on every lag and window feature before training ([Catch a lag that leaks the future](https://rollingedition.com/time-series-forecasting/s/catch-a-lag-that-leaks)) with [the example](https://rollingedition.com/time-series-forecasting/s/catch-a-lag-that-leaks).

**Check:** every kept feature shows zero differing rows, and every holiday year has a non-zero count.

**Pitfalls:**
- A holiday feature decided on ordinary decision windows alone can never be chosen, because none of those days is a holiday ([Measure what each feature adds](https://rollingedition.com/time-series-forecasting/s/measure-what-each-feature-adds)).

## Fit one global model across series

**When to use:** when many series share a shape and every window must forecast all of them.

1. Stack the series into one table, one row per series and hour, and fit once per window. Scale each target with statistics from that window's history only, and convert forecasts back with the same numbers. The scaler at 1.1.0 does this per window ([One model for many clients](https://rollingedition.com/time-series-forecasting/s/one-model-for-many-clients)).
2. Decide the series identifier on decision windows, never the scored cutoffs. Keep it only when it lowers mean per-series MASE, report pooled MAE beside it, and say so if the decision is close ([Identify each client](https://rollingedition.com/time-series-forecasting/s/identify-each-client)) with [the example](https://rollingedition.com/time-series-forecasting/s/identify-each-client).
3. Apply the start rule to every series with leading zeros ([Apply the start rule to every client](https://rollingedition.com/time-series-forecasting/s/apply-the-start-rule-to-every-client)).
4. Score per series against seasonal naive on the same cutoffs, with the book's scale fixed before the first scored cutoff. Print counts of series, windows and scored hours, and name any series left out ([Score thirty clients on the same cutoffs](https://rollingedition.com/time-series-forecasting/s/score-thirty-clients-on-the-same-cutoffs)) with [the example](https://rollingedition.com/time-series-forecasting/s/score-thirty-clients-on-the-same-cutoffs).

**Check:** the report gives counts, refused cutoffs and omitted series, and the mean per-series MASE beside seasonal naive.

**Pitfall:** one model moves every series. Changing one series' zeros can change forecasts for all of them, so after any change, check every series, not only the one you changed ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch6)).

## Make the total add up

**When to use:** when a decision depends on the total of many forecasts, such as the total to buy.

1. Build the total's history as the hourly sum of the series readings. Check on the data that it equals that sum in every hour without a clock-change flag ([Sum the client forecasts](https://rollingedition.com/time-series-forecasting/s/sum-the-client-forecasts)).
2. Forecast the total bottom-up (sum of the series forecasts) and directly (from the total's own history). Score both on the same windows, with seasonal naive on the total ([Forecast the total directly](https://rollingedition.com/time-series-forecasting/s/forecast-the-total-directly), [Compare the two totals](https://rollingedition.com/time-series-forecasting/s/compare-the-two-totals)) with [the example](https://rollingedition.com/time-series-forecasting/s/sum-the-client-forecasts).
3. Keep the method that wins on the decision windows, chosen before scoring. Report both, and the scored cutoffs beside seasonal naive.
4. Split by share only as a baseline or when profiles are alike. Compute each share from history before its cutoff, and check that no share moves when later readings change ([Split a total by share](https://rollingedition.com/time-series-forecasting/s/split-a-total-by-share)) with [the example](https://rollingedition.com/time-series-forecasting/s/split-a-total-by-share).
5. In production, check the total against the sum of its readings on every refit, and stop if a series is missing ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch7)).

**Check:** the total equals the sum of its readings, and bottom-up fails loudly when an hour has too few series forecasts. Confirm that this check fails on a total built with one client removed.

**Pitfalls:**
- When one label holds two hours, a total of raw readings counts that hour at about twice its neighbours. Mask it, and do not halve it ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch7)).

## Quantify uncertainty with conformal intervals

**When to use:** when a decision needs a range, not one number.

1. Ask whether the costs of over- and under-forecasting differ. If they do, give a range and choose its level from the costs ([Why one number is not enough](https://rollingedition.com/time-series-forecasting/s/why-one-number-is-not-enough)).
2. Build each band from a fixed set of earlier calibration windows, each before every scored window, sharing no target hour with them and holding no public holiday. Scale each series' residuals before pooling, a choice made on decision windows ([Build intervals from residuals](https://rollingedition.com/time-series-forecasting/s/build-intervals-from-residuals), [Calibrate on earlier windows](https://rollingedition.com/time-series-forecasting/s/calibrate-on-earlier-windows)) with [the example](https://rollingedition.com/time-series-forecasting/s/calibrate-on-earlier-windows).
3. Read the highest level the residual count can reach before offering any level ([Calibrate on earlier windows](https://rollingedition.com/time-series-forecasting/s/calibrate-on-earlier-windows)) with [the example](https://rollingedition.com/time-series-forecasting/s/build-intervals-from-residuals).
4. Measure coverage on windows the calibration never used, as the share of hours inside the band ([Measure coverage on held-out days](https://rollingedition.com/time-series-forecasting/s/measure-coverage-on-held-out-days)).
5. Set the buy level as `tau = cu / (cu + co)`, with `cu` the cost of one unit short and `co` of one unit over. Fix it before scoring, and show other levels' cost only as a check ([Choose the level from the cost of error](https://rollingedition.com/time-series-forecasting/s/choose-the-level-from-the-cost-of-error)) with [the example](https://rollingedition.com/time-series-forecasting/s/choose-the-level-from-the-cost-of-error).

**Check:** each coverage carries its level and window count.

**Pitfalls:**
- Three scored days say little, and measured coverage is the only check ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch8)).
- Bands pooled in the data's units are set by the largest series. Adding the clients' bounds does not give the total's bound ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch8), [Choose the level from the cost of error](https://rollingedition.com/time-series-forecasting/s/choose-the-level-from-the-cost-of-error)).
- A calibration that uses the cutoffs just before each scored one makes the scored windows depend on each other ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch8)).

## Compare Prophet and recorded models fairly

**When to use:** when a familiar tool or a recorded foundation model is a candidate for the same decision.

1. Set Prophet's seasonality, holidays and interval width in code before scoring, choosing each on decision windows, never the scored cutoffs. Keep a holiday table only if it lowers MASE on holiday decision windows and the ordinary ones, using 1.5.0 ([Run Prophet on the same cutoffs](https://rollingedition.com/time-series-forecasting/s/run-prophet-on-the-same-cutoffs)) with [the example](https://rollingedition.com/time-series-forecasting/s/run-prophet-on-the-same-cutoffs). Set the seed before each predict, and check that a second run prints the same lines.
2. Read Prophet's interval as the level it was set to, and check its coverage against that level ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch9)).
3. Load a recorded model only with its script, pinned revision, package versions and a manifest hashing every output. Check the hashes before any score reads them, and check the weights' licence ([Load a recorded foundation model's forecasts](https://rollingedition.com/time-series-forecasting/s/load-a-recorded-foundation-model)) with [the example](https://rollingedition.com/time-series-forecasting/s/load-a-recorded-foundation-model).
4. Score each recording on the same windows, scale and readings as every other model, and name any interpolated quantile ([Score the recordings on the same cutoffs](https://rollingedition.com/time-series-forecasting/s/score-the-recording-on-the-same-cutoffs)) with [the example](https://rollingedition.com/time-series-forecasting/s/score-the-recording-on-the-same-cutoffs). Check what the model was trained on. If it saw the scored readings, report its score as an upper bound, not as skill.
5. Do not choose a recording for production until it has decision-window forecasts. Score both revisions on the same windows before replacing one ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch9)).

**Check:** the holiday table covers the forecast years, the interval level is printed beside coverage, and each recording covers its cutoffs, orders its quantiles and matches its scored revision.

## Keep the forecast running

**When to use:** when a forecast is produced every day and checked against actuals.

1. Choose the refit cadence on decision windows: ordinary days before the held-out week, on one scale read before them. Take the lower mean MASE, or fewer refits when they are close. Never refit on the day you forecast ([Refit on a schedule](https://rollingedition.com/time-series-forecasting/s/refit-on-a-schedule)) with [the example](https://rollingedition.com/time-series-forecasting/s/refit-on-a-schedule).
2. Write each forecast's rows at its cutoff, from readings that had arrived by then, with the refit day and both arrival times. Never rebuild a past log. Mark a lost day missing ([Log every forecast before its actuals arrive](https://rollingedition.com/time-series-forecasting/s/log-every-forecast-before-actuals)) with [the example](https://rollingedition.com/time-series-forecasting/s/log-every-forecast-before-actuals).
3. Score each day when its last reading arrives, against the forecast logged at its cutoff. A late reading is left out of that cutoff's refit and filled from the same hour a week earlier (a fill chosen on decision windows). Count the fills, and leave the logged forecast alone ([Score the log as actuals arrive](https://rollingedition.com/time-series-forecasting/s/score-the-log-as-actuals-arrive)) with [the example](https://rollingedition.com/time-series-forecasting/s/score-the-log-as-actuals-arrive).
4. Flag a day whose daily MASE is above a factor times the median of the earlier calibration days. The factor of 2 is the book's labelled rule of thumb, with no published threshold. Check on decision windows that no ordinary day is flagged, and record any calendar cause ([Flag drift against the backtest](https://rollingedition.com/time-series-forecasting/s/flag-drift-against-the-backtest)) with [the example](https://rollingedition.com/time-series-forecasting/s/flag-drift-against-the-backtest).
5. Refit early when flags run on several days with no calendar cause, or when the 80% band covers well under 80% of readings on several days. Retire the model when an early refit does not clear them ([Know when to retire a model](https://rollingedition.com/time-series-forecasting/s/know-when-to-retire-a-model)) with [the example](https://rollingedition.com/time-series-forecasting/s/know-when-to-retire-a-model).
6. Keep three checks in every run: the history rule, the two arrival checks, and the leak and poisoning checks ([Check a backtest for leakage](https://rollingedition.com/time-series-forecasting/s/check-a-backtest-for-leakage), [Split a total by share](https://rollingedition.com/time-series-forecasting/s/split-a-total-by-share)). Stop on any failure ([What goes wrong in production](https://rollingedition.com/time-series-forecasting/s/what-goes-wrong-ch10)).

**Check:** the log holds one row per forecast with its cutoff and arrival times, and every flag has a recorded cause or none.

**Pitfalls:**
- A check that compares `written_at` with a reading's arrival passes for any code, because the replay writes `written_at` as the cutoff. Check the arrival times against the cutoff and refit day, and confirm the check fails on a leaky run ([Log every forecast before its actuals arrive](https://rollingedition.com/time-series-forecasting/s/log-every-forecast-before-actuals)).

## Teach this book, when asked

**When:** only when the person you're working with explicitly asks to be taught, tutored or quizzed on this book, one of its chapters or a topic it covers ("teach me", "tutor me", "quiz me", "help me master"). A one-off question ("explain X", "what is X", "how do I use X") gets a normal answer from the procedures above, with no quiz. If you can't tell which they want, ask one short question: a quick answer, or should you teach it properly?

**The topics** are the book's chapters, in order:

1. [Forecast tomorrow's demand](https://rollingedition.com/time-series-forecasting/forecast-tomorrows-demand)
2. [Set the baselines a model must beat](https://rollingedition.com/time-series-forecasting/beat-the-naive-baselines)
3. [Backtest without looking ahead](https://rollingedition.com/time-series-forecasting/backtest-without-looking-ahead)
4. [Fit a statistical model for each client](https://rollingedition.com/time-series-forecasting/fit-statistical-models-per-client)
5. [Add calendar and lag features](https://rollingedition.com/time-series-forecasting/add-calendar-and-lag-features)
6. [Forecast many clients with one model](https://rollingedition.com/time-series-forecasting/forecast-many-clients-at-once)
7. [Make the total add up](https://rollingedition.com/time-series-forecasting/make-the-total-add-up)
8. [Quantify forecast uncertainty](https://rollingedition.com/time-series-forecasting/quantify-forecast-uncertainty)
9. [Compare Prophet and a foundation model](https://rollingedition.com/time-series-forecasting/compare-prophet-and-a-foundation-model)
10. [Keep the forecast running](https://rollingedition.com/time-series-forecasting/keep-the-forecast-running)

For the whole book, show every chapter on the map, and teach one chapter at a time, its sections as its topics. For one chapter, its sections are the topics; for a topic the book covers, the sections that teach it. Keep 4 to 10 topics at a time, joining short sections that follow each other. The Rolling Edition MCP server's `get_contents` lists each chapter's sections, and `get_section` reads one, with its examples.

**Start**

1. Read each section, with `get_section`, before you ask about it. Judge every answer against the book: the section's text, the term's definition from `define` and the output its example recorded, never your memory of a library, which may be another version than this edition's.
2. Say you'll start with a few questions, one at a time, to see what they already know. Ask 3 to 5, from easy to hard, across the topics. Teach nothing until they've answered.
3. Show the map and propose where to start. They can choose another place.

Teach in the language they write in. Where they want a section in that language, see "Reading in another language" below.

**The map.** Each topic has a level from 0 to 5: 0 unaware, 1 heard of it, 2 can follow along, 3 can do it with help, 4 can do it alone, 5 can teach it and handle its edge cases. Show the map after every change of level, and whenever they ask, as a text block with bars of █ and ░:

```text
Forecast tomorrow's demand    overall: █████░░░░░ 53%
------------------------------------------------------------------
The case and its data                      ████████░░  4/5  alone
Load one client's hourly demand            ██████░░░░  3/5  <- now
Forecast the next day with seasonal naive  ██░░░░░░░░  1/5
------------------------------------------------------------------
```

**Teach with questions**

- Ask ONE question in a message, then stop and wait. Add no hints, sample answers or teaching after it.
- Ask them to predict an outcome, explain why, find the flaw in a claim that sounds right, apply an idea to a new case, or connect two ideas.
- Where a topic's section has an example, ask what it prints, or what would change if one line changed, then compare with the output its section shows.
- When they're wrong, don't give the answer. Ask a narrower question that shows the contradiction in their reasoning. Explain directly only after 2 or 3 failed tries, then test the same idea again from another angle.
- When they're right, sometimes push back ("are you sure? what about …?"). They should be able to defend a right answer.
- Explain only what's new and they couldn't work out, in a few sentences from the section, then go back to questions.
- Name the section each question and explanation comes from, with its link: https://rollingedition.com/time-series-forecasting/s/ followed by its ID.

**Levels are earned**

- Raise a level only after two or more separate checks, at least one of them recalled unprompted, not just after you told them the answer.
- A vague or partly right answer isn't right. Probe until you know. Never credit them with an insight they didn't state.
- Now and then, without warning, ask again about an earlier topic. If they miss, lower its level and go back to it.
- Level 5 needs an edge case or a hard question handled, and an explanation you'd trust them to teach from.
- No flattery: "Not quite: why would X happen if Y were true?" beats "Great try!"

**The final exam.** When every topic is at the target level, 4 unless they asked for 5, give a mixed exam: one question for each topic, then one problem that needs several of them together, a task one of the procedures above covers, set somewhere the book doesn't go. If they pass, show the final map and their weakest areas. If not, go back to teaching.

After the exam, tell them once that each chapter's page on rollingedition.com ends with exercises from its examples, and that with Rolling Edition Labs, Submit checks an answer by running it at this edition's pinned versions. Say it plainly, and never make the tutoring wait for it: everything here is free.

**What they can say at any time**

- "show progress": the map.
- "harder" or "easier": change the difficulty.
- "just tell me": answer the current question directly, for that question only. Not for graded work: for an exercise, a quiz or an assignment, point them to its section and help them reason it through.
- "save state": a short block they can paste into a new session, with the book, Edition 2026.11.26 and its code `HVW6-R90X`, the map's levels, the misconceptions you've seen, and what's been covered.
- "resume from:" with a saved block: restore it and go on. If it's from another edition, say so, and ask again about the topics whose sections changed: https://rollingedition.com/time-series-forecasting/changes lists them.

## Reading in another language

When the person you're working with wants to read part of this book in another language, and the Rolling Edition MCP server is connected, first call its `get_section` with `language`: where Rolling Edition has its own translation of the book in that language (`get_contents` lists them), present each section as it comes, with the facts of its `translation`, and translate only the sections it lists as `untranslated`. Otherwise, translate it for them from its sections, read with the Rolling Edition MCP server's `get_section`. Translate the prose faithfully and in full: don't summarize, skip or add anything. Leave these exactly as they are: code, commands, output, file names, identifiers, inline code, package names and versions, numbers and URLs. Where practitioners who read the language usually keep a technical term in English, keep it, and give a short gloss in parentheses the first time, where that helps. Keep the headings and the structure: lists, tables, and the examples in their places. Begin by saying that it's your translation of *Time Series Forecasting*, Edition 2026.11.26, from Rolling Edition, licensed CC BY-NC 4.0, with the chapter's link, and keep each section's link from its citation block. For a long chapter, translate a section at a time and offer to go on after each. The Rolling Edition MCP server's `read_in_my_language` prompt asks for the same.
