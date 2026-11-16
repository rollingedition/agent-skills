"""Tests whether a client identifier lowers the global model's error on four ordinary decision windows, before the
held-out week, on the book's MASE scale. The point rests on the mean per-client MASE lines and on `identifier kept`."""
from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours, mae_change, panel_windows
from lib.quirks import mask_clock_changes
from lib.scoring import actual_hours, book_scale, report_scores, score_windows
from lib.settings import show

raw = load(ALL30)                                             # all thirty clients, not the eight of SUBSET8
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]        # clock-change hours are set to missing, so the scores leave them out
cutoffs = DECISION_CUTOFFS
actual = actual_hours(df, cutoffs)
holiday_hours = check_decision_hours(actual)  # raises before any fit if a scored hour is a holiday or in the held-out week

plain = panel_windows(df, cutoffs, client_id=False, name="plain")               # the model without the identifier
identified = panel_windows(df, cutoffs, client_id=True, name="identifier")      # the same model, with the client as a feature
models = ["plain", "identifier"]
# the MASE scale reads only the readings before the first decision cutoff, so the scored hours cannot leak into it
scored, per_client = score_windows(actual, plain.merge(identified, on=["unique_id", "ds"], validate="one_to_one"),
                                   models, book_scale(raw, cutoffs[0]))
lowers = per_client["identifier"] < per_client["plain"]
size = raw.groupby("unique_id")["y"].mean().sort_values(ascending=False)   # mean kWh per client, largest first
contrib = mae_change(scored, "plain", "identifier")           # each client's share of the pooled MAE change, kWh; the shares sum to the total

show("first decision cutoff", f"{cutoffs[0]:%Y-%m-%d}")
show("last decision cutoff", f"{cutoffs[-1]:%Y-%m-%d}")
show("clients", scored["unique_id"].nunique())
show("windows", len(cutoffs))
show("scored hours", len(scored))
show("decision hours on a holiday", holiday_hours)
report_scores(scored, per_client, models)
show("clients where the identifier lowers MASE", int(lowers.sum()))
show("of the 15 largest clients, where the identifier lowers MASE", int(lowers[size.index[:15]].sum()))
show("of the 15 smallest clients, where the identifier lowers MASE", int(lowers[size.index[-15:]].sum()))
show("largest client", size.index[0])
show("pooled MAE change from the largest client, kWh", contrib[size.index[0]])
show("pooled MAE change, all clients, kWh", contrib.sum())
# the decision rule keeps the identifier only if the mean per-client MASE is lower, not the pooled MAE
show("identifier kept", "yes" if per_client["identifier"].mean() < per_client["plain"].mean() else "no")
