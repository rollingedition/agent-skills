"""Test whether a client identifier lowers the global model's per-client error, on the four decision cutoffs of late
November and early December 2014. They come before the held-out week and hold no Portuguese holiday. The identifier is
the only difference between the two runs. The MASE scale is the book's (scoring.book_scale), read from the first cutoff."""
from lib.electricity import load
from lib.panel import ALL30, DECISION_CUTOFFS, check_decision_hours, mae_change, panel_windows
from lib.quirks import mask_clock_changes
from lib.scoring import actual_hours, book_scale, report_scores, score_windows
from lib.settings import show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
cutoffs = DECISION_CUTOFFS
actual = actual_hours(df, cutoffs)
holiday_hours = check_decision_hours(actual)  # raises if a scored hour is a holiday or in the held-out week

plain = panel_windows(df, cutoffs, client_id=False, name="plain")
identified = panel_windows(df, cutoffs, client_id=True, name="identifier")
models = ["plain", "identifier"]
scored, per_client = score_windows(actual, plain.merge(identified, on=["unique_id", "ds"], validate="one_to_one"),
                                   models, book_scale(raw, cutoffs[0]))
lowers = per_client["identifier"] < per_client["plain"]
size = raw.groupby("unique_id")["y"].mean().sort_values(ascending=False)
contrib = mae_change(scored, "plain", "identifier")

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
show("identifier kept", "yes" if per_client["identifier"].mean() < per_client["plain"].mean() else "no")
