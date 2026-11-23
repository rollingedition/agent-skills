"""Compare each release with baseline r0 on the same messages, in message time and input tokens: the mean of the per-message differences, and the p95 difference with the two p95s resampled jointly (PL-6). Each interval is a bootstrap of 2,000 resamples at 95 %, seed 20261207. The unpaired width for the input tokens is printed beside the paired one: the messages' own lengths cancel out of the paired difference."""
from lib.gate import measured, paired, paired_report

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
RELEASES_TO_COMPARE = [   # name, the release's recording folder, the model it ran
    ("r1", "release-prompt-v2", MODEL),       # p2: six routing examples in the route prompt
    ("r2", "release-model-swap", "Qwen3-0.6B"),
    ("r3", "release-top-8", MODEL),            # top 8 articles instead of 3
    ("r4", "release-cache-off", MODEL),        # a fresh state per call, so no cached prefix
]
base = measured("baseline-day-1", DAY, MODEL)  # r0, the cache on, on all 200 messages of baseline day 1
for name, folder, model in RELEASES_TO_COMPARE:
    _, before, after = paired(base, measured(folder, DAY, model))   # the messages this release recorded
    paired_report(name, before, after)
