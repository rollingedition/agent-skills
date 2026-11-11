"""Check the recorded NHITS outputs before any score reads them: the file's SHA-256 against manifest.json, the shape of the
forecast file, and whether any row's quantiles run out of order. NHITS is not run; the recording is read."""
from lib.compare import check_recording
from lib.settings import show

for label, value in check_recording("nhits").items():
    show(label, value)
