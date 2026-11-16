"""Shift test: a feature must read nothing from its cutoff on, on the history rows and on the target hours. The prose's
point rests on the counts of differing rows: an honest feature shows zero, and a leaking one shows its leak."""
from lib.electricity import load
from lib.leakage import history_test, lag, peeking_mean, target_test, trailing_mean
from lib.settings import EVAL_CUTOFFS, LEAD, show

y = load([LEAD]).set_index("ds")["y"]  # indexed by timestamp, so each feature can be cut at a cutoff by time

compared, honest = history_test(y, trailing_mean)  # rows compared, and the rows where cutting at the cutoff changes the feature
_, peeking = history_test(y, peeking_mean)  # the leaking feature: its last value before each cutoff reads the cutoff hour
_, lag1_history = history_test(y, lag(1))  # lag 1 reads only the past on history rows, so this half passes it
show("cutoffs", len(EVAL_CUTOFFS))
show("rows compared", compared)
show("rows differing for the trailing mean", honest)
show("rows differing for the peeking mean", peeking)
show("rows differing for lag 1", lag1_history)

targets, lag1_target = target_test(y, lag(1))  # target hours compared, and the hours that differ, over the 24 hours of each cutoff
_, lag24_target = target_test(y, lag(24))
show("target hours compared", targets)
show("target hours differing for lag 1", lag1_target)
show("target hours differing for lag 24", lag24_target)
