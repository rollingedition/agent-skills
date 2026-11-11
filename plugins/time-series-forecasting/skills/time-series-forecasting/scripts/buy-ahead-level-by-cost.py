"""The buy level for the total, from the two costs. The critical fractile, cu / (cu + co), is the quantile that minimises
the expected cost. The example prints the costs, the total's 80 percent bands with their coverage by day, the realised cost
of three levels on the three standard cutoffs, and the total's bound against the sum of the clients' bounds. The costs are
illustrative; they are not prices."""
import pandas as pd

from lib.electricity import load
from lib.intervals import CAL_CUTOFFS, COST_EXCESS, COST_SHORT, buy_report, critical_fractile, paired
from lib.panel import ALL30
from lib.quirks import mask_clock_changes
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
df = mask_clock_changes(raw)[["unique_id", "ds", "y"]]
pairs_cal, pairs_sc = paired(df, CAL_CUTOFFS), paired(df, pd.to_datetime(EVAL_CUTOFFS))

show("cost of a kWh short", COST_SHORT)
show("cost of a kWh unused", COST_EXCESS)
show("critical fractile", critical_fractile())
for label, value, digits in buy_report(pairs_cal, pairs_sc):
    show(label, value, digits)
