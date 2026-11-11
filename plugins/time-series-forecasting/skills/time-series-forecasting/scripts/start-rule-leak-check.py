"""Check that the start rule reads only rows before each cutoff, refuses the cutoffs the data's flag predicts, and removes
only leading zeros. The same checks run on a deliberately broken history function, to show that each check can fail.
The checks themselves are start_rule_checks in lib/panel.py."""
import pandas as pd

from lib.electricity import load
from lib.panel import ALL30, FEBRUARY_CUTOFFS, leaky_history, panel_history, start_rule_checks
from lib.settings import EVAL_CUTOFFS, show

raw = load(ALL30)
CHECKED = pd.DatetimeIndex(["2013-12-15", "2014-01-01", "2014-01-15", *FEBRUARY_CUTOFFS, *EVAL_CUTOFFS])


def report(prefix, r):
    show(f"{prefix}cutoffs checked", len(CHECKED))
    show(f"{prefix}cutoffs refused by the start rule", r["refused"])
    show(f"{prefix}cutoffs expected to be refused, from the flag", r["expected"])
    show(f"{prefix}cutoffs where the refusal differs from the flag", r["mismatch"])
    show(f"{prefix}cutoffs accepted", r["accepted"])
    show(f"{prefix}accepted cutoffs with a client missing from the history", r["missing"])
    show(f"{prefix}cutoffs whose history changes when the future is poisoned", r["changed"])


real = start_rule_checks(raw, CHECKED, panel_history, removed_rows=True)
report("", real)
show("rows the start rule removes, accepted cutoffs", real["removed"])
show("removed rows that are not zero", real["removed_nonzero"])
report("broken version, ", start_rule_checks(raw, CHECKED, leaky_history))
