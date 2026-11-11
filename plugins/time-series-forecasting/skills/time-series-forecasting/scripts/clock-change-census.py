"""The clock-change hours of all thirty clients: how many read zero, and how each compares with its neighbours."""
from lib.electricity import load
from lib.quirks import clock_ratios
from lib.settings import show

r = clock_ratios(load())
gap = r[r["quirk"] == "clock_change_gap"]
repeat = r[r["quirk"] == "clock_change_repeat"]
show("gap rows", len(gap))
show("gap rows that read zero", int((gap["y"] == 0).sum()))
show("gap rows that read above zero", int((gap["y"] > 0).sum()))
show("gap rows below 5 percent of their neighbours", int((gap["ratio"] < 0.05).sum()))
show("gap rows at or above 5 percent of their neighbours", int((gap["ratio"] >= 0.05).sum()))
show("median gap ratio to neighbours", gap["ratio"].median(), digits=3)
show("repeat rows", len(repeat))
show("median repeat ratio to neighbours", repeat["ratio"].median(), digits=3)
