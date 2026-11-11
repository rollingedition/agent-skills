"""Forecast all thirty clients with one global LightGBM on the three standard cutoffs, with the start rule applied to each
client and the client identifier kept by client-identifier-check. Score it beside seasonal naive on the same windows,
per client against the book's MASE scale. The model without the identifier is printed for reference."""
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import SeasonalNaive

from lib.backtest import forecast_windows
from lib.baselines import SEASON
from lib.electricity import load
from lib.panel import ALL30, IDENTIFIER_KEPT, panel_windows
from lib.quirks import mask_clock_changes
from lib.scoring import actual_hours, book_scale, left_out_facts, report_scores, score_windows
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = pd.to_datetime(EVAL_CUTOFFS)
actual = actual_hours(df, cutoffs)

naive = forecast_windows(StatsForecast(models=[SeasonalNaive(season_length=SEASON)], freq="h", n_jobs=1), df, cutoffs)
global_fc = panel_windows(df, cutoffs, client_id=IDENTIFIER_KEPT)
plain_fc = panel_windows(df, cutoffs, client_id=False, name="plain")
forecasts = naive.merge(global_fc, on=["unique_id", "ds"], validate="one_to_one").merge(
    plain_fc, on=["unique_id", "ds"], validate="one_to_one")
models = ["SeasonalNaive", "global", "plain"]
scored, per_client = score_windows(actual, forecasts, models, book_scale(raw, cutoffs[0]))
beats = per_client["global"] < per_client["SeasonalNaive"]

show("clients scored", scored["unique_id"].nunique())
show("windows", len(cutoffs))
show("scored hours", len(scored))
for label, value in left_out_facts(raw, df, cutoffs[0]).items():
    show(label, value)
show("clients in MASE", per_client["global"].notna().sum())
show("clients where global beats seasonal naive", int(beats.sum()))
show("clients where seasonal naive wins", ", ".join(sorted(per_client.index[~beats])))
report_scores(scored, per_client, models)
