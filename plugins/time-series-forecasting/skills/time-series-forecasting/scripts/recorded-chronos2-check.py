"""Checks the recorded Chronos-2 outputs before any score reads them: each file's SHA-256 against manifest.json, the
shape of the forecast file, and any quantiles out of order, without running the model. The point that the recording
is intact rests on the hash mismatches line and the rows with quantiles out of order line."""
from lib.compare import check_recording
from lib.settings import show

for label, value in check_recording().items():   # the default name is the chronos-2 folder in examples/data/recorded/
    show(label, value)
