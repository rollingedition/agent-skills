"""Shift test: a feature must read nothing from its cutoff on, on the history rows and on the target hours."""
from lib.electricity import load
from lib.leakage import history_test, lag, peeking_mean, target_test, trailing_mean
from lib.settings import EVAL_CUTOFFS, LEAD, show

y = load([LEAD]).set_index("ds")["y"]

compared, honest = history_test(y, trailing_mean)
_, peeking = history_test(y, peeking_mean)
_, lag1_history = history_test(y, lag(1))
show("cutoffs", len(EVAL_CUTOFFS))
show("rows compared", compared)
show("rows differing for the trailing mean", honest)
show("rows differing for the peeking mean", peeking)
show("rows differing for lag 1", lag1_history)

targets, lag1_target = target_test(y, lag(1))
_, lag24_target = target_test(y, lag(24))
show("target hours compared", targets)
show("target hours differing for lag 1", lag1_target)
show("target hours differing for lag 24", lag24_target)
