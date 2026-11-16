"""Runs the global model with the start rule and without it, on the February cutoffs, where a late starter's zeros enter
the history, and on the standard cutoffs, where the rule changes no row. The point rests on the February mean MASE lines
and the count of forecast hours that differ; the scale lines compare the book's scale with a labelled counterfactual."""
import numpy as np
import pandas as pd

from lib.electricity import load
from lib.panel import (ALL30, FEBRUARY_CUTOFFS, IDENTIFIER_KEPT, LATE_STARTERS, late_starter_facts, mae_by_group,
                       mase_by_run, scale_facts, with_and_without_start_rule)
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]        # clock-change hours are set to missing, so the scores leave them out
for label, value in late_starter_facts(raw, df).items():
    show(label, value)

standard = pd.to_datetime(EVAL_CUTOFFS)                       # the three standard cutoffs
# two runs of the same model on the same cutoffs, differing only in their histories
scored = with_and_without_start_rule(df, standard, client_id=IDENTIFIER_KEPT)
# compared with isclose, so a rounding difference between two runs does not count as a changed forecast
show("forecast hours that differ, standard", int((~np.isclose(scored["start"], scored["raw"])).sum()))

# the February cutoffs, where the zeros of MT_115 and MT_179 enter the history
feb = with_and_without_start_rule(df, FEBRUARY_CUTOFFS, client_id=IDENTIFIER_KEPT)
show("scored hours, february", len(feb))
show("forecast hours that differ, february", int((~np.isclose(feb["start"], feb["raw"])).sum()))
for model in ["start", "raw"]:
    for group, value in mae_by_group(feb, model).items():
        show(f"MAE {group}, {model}, february", value)
# both runs on one scale, read from the first February cutoff
feb_mase = mase_by_run(raw, feb, ["start", "raw"])
show("clients in MASE, february", int(feb_mase["start"].notna().sum()))
for uid in LATE_STARTERS:
    show(f"MASE {uid}, start, february", feb_mase.loc[uid, "start"])
    show(f"MASE {uid}, raw, february", feb_mase.loc[uid, "raw"])
for run in ["start", "raw"]:
    show(f"mean MASE, {run}, february", feb_mase[run].mean())

# 'counterfactual raw' keeps the zeros before each first reading, a scale the book does not use; 'start rule' is the book's
for label, value in scale_facts(raw, standard, IDENTIFIER_KEPT).items():
    show(label, value)
