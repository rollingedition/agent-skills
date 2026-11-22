"""Draw each client's MASE under seasonal naive against the global model's, on the three standard cutoffs, with the equal line.
Clients above the line are the ones seasonal naive wins; they are labelled. The forecasts and scale are global-model-thirty-clients's."""
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows
from lib.baselines import SEASON
from lib.electricity import load
from lib.figures import ACCENT, INK, MUTED, new_figure, save
from lib.panel import ALL30, IDENTIFIER_KEPT, panel_windows
from lib.quirks import mask_clock_changes
from lib.scoring import actual_hours, book_scale, score_windows
from lib.settings import EVAL_CUTOFFS, show

NARROW = 0.1                                                    # a seasonal naive win by less than this is narrow
df = mask_clock_changes(raw := load(ALL30))[["unique_id", "ds", "y"]]          # clock-change hours masked, as in global-model-thirty-clients
cutoffs = pd.to_datetime(EVAL_CUTOFFS)
naive = forecast_windows(StatsForecast(models=[SeasonalNaive(season_length=SEASON)], freq="h", n_jobs=1), df, cutoffs)
forecasts = naive.merge(panel_windows(df, cutoffs, client_id=IDENTIFIER_KEPT), on=["unique_id", "ds"], validate="one_to_one")
_, per_client = score_windows(actual_hours(df, cutoffs), forecasts, ["SeasonalNaive", "global"], book_scale(raw, cutoffs[0]))

wins = per_client["global"] < per_client["SeasonalNaive"]       # the strict test global-model-thirty-clients uses
margin = (per_client["global"] - per_client["SeasonalNaive"])[~wins]   # how far the global model trails, on seasonal naive's wins
show("clients where seasonal naive has the lower MASE", len(margin))
show("margin that counts as narrow, MASE", NARROW)
show("clients where seasonal naive wins by less than that margin", int((margin < NARROW).sum()))
show("largest margin where seasonal naive wins, MASE", margin.max())
show("client with the largest margin", margin.idxmax())

lo, hi = 0, per_client.max().max() * 1.05                       # from zero, so no point sits on an axis limit
fig, ax = new_figure(height=3.4)
ax.plot([lo, hi], [lo, hi], color=INK, linestyle="--", linewidth=1.0, label="equal MASE")
for mask, color, label in ((wins, MUTED, "global model lower"), (~wins, ACCENT, "seasonal naive lower")):
    ax.scatter(per_client.loc[mask, "SeasonalNaive"], per_client.loc[mask, "global"], s=20, color=color, label=label)
ax.set(xlim=(lo, hi), ylim=(lo, hi), xlabel="MASE under seasonal naive", ylabel="MASE under the global model")

# each label takes the spot farthest, in axes units, from every point and label already placed
pos = list(ax.transAxes.inverted().transform(ax.transData.transform(per_client[["SeasonalNaive", "global"]].to_numpy())))
for uid in margin.index:
    here = pos[per_client.index.get_loc(uid)]
    spots = [(here[0] + dx, here[1] + dy) for dx in (0.03, -0.03, 0.07, -0.07) for dy in (0.04, -0.04, 0.09, -0.09)]
    spot = max([s for s in spots if 0.12 < s[0] < 0.88 and 0.05 < s[1] < 0.95], key=lambda s: min(abs(s[0] - t[0]) + abs(s[1] - t[1]) for t in pos))
    ax.annotate(uid, xy=tuple(per_client.loc[uid]), xytext=spot, textcoords="axes fraction", color=ACCENT, fontsize=8,
                ha="left" if spot[0] > here[0] else "right", arrowprops=dict(arrowstyle="-", color=ACCENT, linewidth=0.5))
    pos.append(spot)
fig.legend(loc="outside upper left", ncols=3, frameon=False, labelcolor=INK)
save(fig, "client-mase-global-vs-naive")
