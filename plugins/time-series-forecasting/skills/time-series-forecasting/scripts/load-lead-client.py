"""Load the lead client's hourly demand, count its quirks, and check the held-out histories."""
from lib.backtest import held_out_cutoffs, history_before
from lib.electricity import load
from lib.settings import LEAD, show


def fmt(ts):
    return ts.strftime("%Y-%m-%d %H:%M")


FULL_ROWS = 2 * 365 * 24  # two years of hours; 2013 and 2014 are not leap years

everyone = load()
show("clients in the file", everyone["unique_id"].nunique())
show(f"clients with {FULL_ROWS} rows", int((everyone.groupby("unique_id").size() == FULL_ROWS).sum()))

df = load([LEAD])
show("rows", len(df))
show("first reading", fmt(df["ds"].min()))
show("last reading", fmt(df["ds"].max()))
for quirk in ["normal", "before_first_reading", "clock_change_gap", "clock_change_repeat"]:
    show(f"{quirk} rows", int((df["quirk"] == quirk).sum()))

windows = [history_before(df, cutoff) for cutoff in held_out_cutoffs()]
show("history rows per window", min(len(w) for w in windows))
show("longest history rows", max(len(w) for w in windows))
show("first history reading", fmt(windows[0]["ds"].min()))
show("clock-change rows in held-out histories",
     sum(int(w["quirk"].isin(["clock_change_gap", "clock_change_repeat"]).sum()) for w in windows))
