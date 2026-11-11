"""Run the global model with and without the start rule. On the February cutoffs of Chapter 4, where a late starter's zeros
enter the history, both runs are scored on the one book scale. On the standard cutoffs the start rule changes no row, and
the scale is compared with a labelled counterfactual that keeps the zeros (not the book's rule)."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.panel import (ALL30, FEBRUARY_CUTOFFS, IDENTIFIER_KEPT, LATE_STARTERS, late_starter_facts, mae_by_group,
                       mase_by_run, scale_facts, with_and_without_start_rule)
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
for label, value in late_starter_facts(raw, df).items():
    show(label, value)

standard = pd.to_datetime(EVAL_CUTOFFS)
scored = with_and_without_start_rule(df, standard, client_id=IDENTIFIER_KEPT)
show("forecast hours that differ, standard", int((~np.isclose(scored["start"], scored["raw"])).sum()))

feb = with_and_without_start_rule(df, FEBRUARY_CUTOFFS, client_id=IDENTIFIER_KEPT)
show("scored hours, february", len(feb))
show("forecast hours that differ, february", int((~np.isclose(feb["start"], feb["raw"])).sum()))
for model in ["start", "raw"]:
    for group, value in mae_by_group(feb, model).items():
        show(f"MAE {group}, {model}, february", value)
feb_mase = mase_by_run(raw, feb, ["start", "raw"])
show("clients in MASE, february", int(feb_mase["start"].notna().sum()))
for uid in LATE_STARTERS:
    show(f"MASE {uid}, start, february", feb_mase.loc[uid, "start"])
    show(f"MASE {uid}, raw, february", feb_mase.loc[uid, "raw"])
for run in ["start", "raw"]:
    show(f"mean MASE, {run}, february", feb_mase[run].mean())

for label, value in scale_facts(raw, standard, IDENTIFIER_KEPT).items():
    show(label, value)
