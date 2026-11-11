"""Check the recorded Chronos-2 outputs before any score reads them: each file's SHA-256 against manifest.json, the shape
of the forecast file, and whether any row's quantiles run out of order. The model is not run; the recording is read."""
from lib.compare import check_recording
from lib.settings import show

for label, value in check_recording().items():
    show(label, value)
