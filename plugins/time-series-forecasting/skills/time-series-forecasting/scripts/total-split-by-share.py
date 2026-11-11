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
