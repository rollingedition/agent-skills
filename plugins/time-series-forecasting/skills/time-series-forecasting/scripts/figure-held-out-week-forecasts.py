"""Draw the lead client's actual load over the held-out week, with the seasonal naive and AutoETS forecasts made at each midnight cutoff.
The prose rests on the two days at Christmas: the baseline's Dec 26 forecast equals Dec 25's readings hour by hour, and AutoETS's daily mean is above the load on Dec 25 and below it on Dec 26."""
import matplotlib.dates as mdates
import numpy as np
from statsforecast import StatsForecast
from statsforecast.models import AutoETS, SeasonalNaive

from lib.backtest import forecast_windows, held_out_cutoffs
from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.settings import LEAD, show

# The same two models, settings and cutoffs as the two examples, so these are the forecasts they score.
df = load([LEAD])[["unique_id", "ds", "y"]]
sf = StatsForecast(models=[SeasonalNaive(season_length=24), AutoETS(season_length=24, model="ZZA")], freq="h", n_jobs=1)
forecasts = forecast_windows(sf, df, held_out_cutoffs())

# One row per scored hour: each model's forecast beside the reading.
joined = forecasts.merge(df[["ds", "y"]], on="ds").set_index("ds").sort_index()
xmas, boxing = joined.loc["2014-12-25"], joined.loc["2014-12-26"]   # a partial date string selects that whole day

show("scored hours", len(joined))
show("mean load on Dec 25, kWh", xmas["y"].mean())
show("mean load on Dec 26, kWh", boxing["y"].mean())
show("seasonal naive mean on Dec 26, kWh", boxing["SeasonalNaive"].mean())
show("AutoETS mean on Dec 25, kWh", xmas["AutoETS"].mean())
show("AutoETS mean on Dec 26, kWh", boxing["AutoETS"].mean())
# Seasonal naive with a season of 24 repeats the last day's readings, so Dec 26 is Dec 25 read hour by hour.
assert np.allclose(boxing["SeasonalNaive"].to_numpy(), xmas["y"].to_numpy())
assert xmas["AutoETS"].mean() > xmas["y"].mean()      # AutoETS expects more than the load on Christmas Day
assert boxing["AutoETS"].mean() < boxing["y"].mean()  # and less than the load the day after

fig, ax = new_figure(height=3.2)
ax.plot(joined.index, joined["y"], color=INK, linewidth=1.8, label="actual load")
ax.plot(joined.index, joined["AutoETS"], color=MUTED, linewidth=1.2, marker="o", markersize=2.5, label="AutoETS")
ax.plot(joined.index, joined["SeasonalNaive"], color=ACCENT, linestyle="--", linewidth=1.4, label="seasonal naive")
ax.set_ylabel("kWh in the hour")
ax.set_ylim(bottom=0)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %-d"))
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "held-out-week-forecasts")
