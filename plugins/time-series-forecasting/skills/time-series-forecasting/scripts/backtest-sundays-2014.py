"""Seasonal naive over the 52 Sunday cutoffs of 2014 for the subset of eight clients, with no rule applied."""
import pandas as pd
from holidays import country_holidays
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows, history_before
from lib.electricity import load
from lib.quirks import year_scores
from lib.scoring import book_scale, clients_left_out
from lib.settings import HORIZON, SUBSET8, show

COLS = ["unique_id", "ds", "y"]
cutoffs = pd.date_range("2014-01-05", "2014-12-28", freq="W-SUN")  # 52 Sundays, both clock changes among them
df = load(SUBSET8)[COLS + ["quirk"]]
sf = StatsForecast(models=[SeasonalNaive(season_length=24)], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df[COLS], cutoffs, h=HORIZON)
scored = forecasts.merge(df, on=["unique_id", "ds"])
scale = book_scale(df, cutoffs[0])  # the MASE scale: every reading before the first cutoff, from 2013 on
sizes = pd.concat([history_before(df, c).groupby("unique_id").size() for c in cutoffs])
holidays = country_holidays("PT", years=[2014])

show("windows", len(cutoffs))
show("history hours per series, min over windows", sizes.min())
show("history hours per series, max over windows", sizes.max())
show("Sunday windows on a Portuguese holiday", sum(c.date() in holidays for c in cutoffs))
show("client left out of MASE", ", ".join(clients_left_out(df, cutoffs[0])))
for label, value in year_scores(scored, scale).items():
    show(label, value)
