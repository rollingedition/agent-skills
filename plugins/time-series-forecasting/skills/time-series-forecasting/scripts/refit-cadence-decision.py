"""Choose the refit cadence on the decision windows, Nov 25 to Dec 3, 2014. Both cadences forecast every day from its own
cutoff with the global model from Chapter 6. They differ only in how often its parameters are re-estimated: every day, or
every seven days, on Mondays. The held-out week is not used. The last check forecasts each decision day from a model
aged 0 to 6 days, so the claim can be sized to the ages a weekly cadence produces."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30
from lib.running import DECISION_DAYS, daily_mase, feed, fit_at, forecast_at, prepare, run_days, scale_from, with_actuals
from lib.settings import show

raw = load(ALL30)
df = prepare(raw)
scale = scale_from(raw)
show("decision days", len(DECISION_DAYS))
show("rows read by one refit", len(feed(df, DECISION_DAYS[0])[0]))
names = {1: "daily", 7: "weekly"}
means = {}
for every in names:
    scored = with_actuals(run_days(df, DECISION_DAYS, refit_every=every), df)
    means[every] = daily_mase(scored, scale).mean()
    show(f"refits, {names[every]}", scored["refit"].nunique())
    show(f"MAE, {names[every]}", scored["ae"].mean())
    show(f"mean MASE, {names[every]}", means[every], digits=3)
show("mean MASE, daily minus weekly", means[1] - means[7], digits=3)
show("chosen cadence", names[min(means, key=means.get)])
models = {}
for age in range(7):
    parts = []
    for day in DECISION_DAYS:
        fit_day = day - pd.Timedelta(days=age)
        if fit_day not in models:
            models[fit_day] = fit_at(df, fit_day)[0]
        part, _, _ = forecast_at(models[fit_day], df, day)
        parts.append(part.assign(cutoff=day))
    show(f"mean MASE, model aged {age} days", daily_mase(with_actuals(pd.concat(parts), df), scale).mean(), digits=3)
