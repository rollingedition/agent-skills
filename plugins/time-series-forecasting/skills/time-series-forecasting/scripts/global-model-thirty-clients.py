"""Scores one global LightGBM model, with the identifier that client-identifier-check kept, against seasonal naive on the
three standard cutoffs, per client on the book's MASE scale. The point rests on the mean per-client MASE lines; the model
without the identifier is printed for reference only."""
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
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]        # clock-change hours are set to missing, so the scores leave them out
cutoffs = pd.to_datetime(EVAL_CUTOFFS)                        # the three standard cutoffs, Dec 29 to Dec 31, 2014
actual = actual_hours(df, cutoffs)

# seasonal naive from each cutoff's own history: the baseline of Chapter 2
naive = forecast_windows(StatsForecast(models=[SeasonalNaive(season_length=SEASON)], freq="h", n_jobs=1), df, cutoffs)
global_fc = panel_windows(df, cutoffs, client_id=IDENTIFIER_KEPT)   # the identifier setting that client-identifier-check kept
plain_fc = panel_windows(df, cutoffs, client_id=False, name="plain")  # the same model without the identifier, for reference
forecasts = naive.merge(global_fc, on=["unique_id", "ds"], validate="one_to_one").merge(
    plain_fc, on=["unique_id", "ds"], validate="one_to_one")
models = ["SeasonalNaive", "global", "plain"]
# the book's scale, read from the readings before the first cutoff only
scored, per_client = score_windows(actual, forecasts, models, book_scale(raw, cutoffs[0]))
beats = per_client["global"] < per_client["SeasonalNaive"]    # per client: True where the global model's MASE is lower

show("clients scored", scored["unique_id"].nunique())
show("windows", len(cutoffs))
show("scored hours", len(scored))
# a client with no non-zero reading before the first cutoff is left out of MASE, and is not an error
for label, value in left_out_facts(raw, df, cutoffs[0]).items():
    show(label, value)
show("clients in MASE", per_client["global"].notna().sum())
show("clients where global beats seasonal naive", int(beats.sum()))
show("clients where seasonal naive wins", ", ".join(sorted(per_client.index[~beats])))
report_scores(scored, per_client, models)
