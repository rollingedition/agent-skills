"""Splits the direct total forecast into client forecasts, each client taking its share of the history before each cutoff
(top-down), and compares them with bottom-up on the same windows. The point rests on the mean per-client MASE and MAE lines;
the last line is a leak check that no share reads a reading after its cutoff."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours
from lib.settings import EVAL_CUTOFFS, show
from lib.totals import SPLIT_METHODS, client_mae, oracle_split_mae, shares, split_checks, split_scored

raw = load(ALL30)
dec, cut = pd.to_datetime(DECISION_CUTOFFS), pd.to_datetime(EVAL_CUTOFFS)

# the third value, the hours the top-down clients don't add up to the direct total (none, by construction), is unused
dec_scored, dec_per, _ = split_scored(raw, dec)
show("decision holiday hours", check_decision_hours(dec_scored))
show("mean per-client MASE bottom-up, decision windows", dec_per["bottom-up"].mean())
show("mean per-client MASE top-down, decision windows", dec_per["top-down"].mean())
show("chosen client method", dec_per.mean().idxmin())

# the third value is discarded, as above
scored, per_client, _ = split_scored(raw, cut)
show("scored hours", len(scored))
mae = pd.DataFrame({m: client_mae(scored, m) for m in SPLIT_METHODS})
for model in SPLIT_METHODS:
    show(f"mean per-client MAE {model}", mae[model].mean())
for model in SPLIT_METHODS:
    show(f"mean per-client MASE {model}", per_client[model].mean())
show("clients where top-down has the lower MAE", int((mae["top-down"] < mae["bottom-up"]).sum()))
# the split applied to the actual total: a reference, since no forecast can know the total in advance
show("mean per-client MAE with the true total split by share", oracle_split_mae(raw, cut))
# the first standard cutoff, Dec 29, 2014; its shares read only the history before it
# shares read the 1,344 hours (8 weeks) before the cutoff
show("largest client share of the total, first cutoff", shares(raw, cut[0]).max())
# each cutoff's readings from the cutoff on replaced by zero, then by a very large value
for label, value in split_checks(raw, cut).items():
    show(label, value)
