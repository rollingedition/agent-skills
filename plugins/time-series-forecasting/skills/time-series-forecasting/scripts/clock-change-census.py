"""The clock-change hours of all thirty clients, each against its neighbours. The point that the March hours read near zero
rests on the gap rows below 5 percent of their neighbours, with the zero count and the median ratio beside them."""
from lib.electricity import load
from lib.quirks import clock_ratios
from lib.settings import show

r = clock_ratios(load())  # each clock-change hour divided by the mean of the hour before and the hour after
gap = r[r["quirk"] == "clock_change_gap"]  # the file's flag: 01:00 on the March change day, an hour the clock skips
repeat = r[r["quirk"] == "clock_change_repeat"]  # the file's flag: 01:00 holds two hours on the October change day
show("gap rows", len(gap))
show("gap rows that read zero", int((gap["y"] == 0).sum()))
show("gap rows that read above zero", int((gap["y"] > 0).sum()))
show("gap rows below 5 percent of their neighbours", int((gap["ratio"] < 0.05).sum()))  # a NaN ratio, where both neighbours are zero, counts in neither line
show("gap rows at or above 5 percent of their neighbours", int((gap["ratio"] >= 0.05).sum()))
show("median gap ratio to neighbours", gap["ratio"].median(), digits=3)
show("repeat rows", len(repeat))
show("median repeat ratio to neighbours", repeat["ratio"].median(), digits=3)
