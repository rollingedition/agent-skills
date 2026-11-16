"""Checks the recorded NHITS outputs before any score reads them: each file's SHA-256 against manifest.json, the shape
of the forecast file, and any quantiles out of order, without running the model. The point that the recording is
intact rests on the hash mismatches line; the interpolated levels line shows that every level is trained directly, and
the rows with quantiles out of order line is the one the chapter reports."""
from lib.compare import check_recording
from lib.settings import show

for label, value in check_recording("nhits").items():   # "nhits" is the NHITS folder in examples/data/recorded/
    show(label, value)
