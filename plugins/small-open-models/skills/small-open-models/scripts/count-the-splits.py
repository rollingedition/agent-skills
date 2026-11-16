"""Count each BANKING77 split and its messages per team, and check the committed samples; no model runs.

The prose's point rests on the four "per label" lines for the test and training files.
"""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from collections import Counter  # noqa: E402

router_lib.setup_runtime()

train = router_lib.read_rows("train")
test = router_lib.read_rows("test")
dev = router_lib.read_sample("dev")  # dev row numbers index train.csv, never test.csv

assert len(set(dev)) == len(dev), "dev indices repeat"
assert max(dev) < len(train), "dev indices fall outside train.csv"

train_per_label = Counter(label for _, label in train)
test_per_label = Counter(label for _, label in test)

test_1001 = router_lib.read_sample("test_1001")  # committed order: prefixes are the first n of it
test_40 = router_lib.read_sample("test_40")
test_200 = router_lib.read_sample("test_200")
# test_40 and test_200 are prefixes of the shuffled order, not new draws
assert test_1001[:40] == test_40, "test_40 is not the first 40 of test_1001"
assert test_1001[:200] == test_200, "test_200 is not the first 200 of test_1001"
sample_per_label = Counter(test[i][1] for i in test_1001)  # rows are (text, label index); [1] is the label

train_counts = [train_per_label[i] for i in range(len(router_lib.LABELS))]  # one entry per team, so a team with no rows counts 0
test_counts = [test_per_label[i] for i in range(len(router_lib.LABELS))]
sample_counts = [sample_per_label[i] for i in range(len(router_lib.LABELS))]

print(f"train rows: {len(train)}")
print(f"dev rows: {len(dev)}")
print(f"test rows: {len(test)}")
print(f"labels: {len(router_lib.LABELS)}")
print(f"test per label min: {min(test_counts)}")
print(f"test per label max: {max(test_counts)}")
print(f"train per label min: {min(train_counts)}")
print(f"train per label max: {max(train_counts)}")
print(f"test_1001 per label min: {min(sample_counts)}")
print(f"test_1001 per label max: {max(sample_counts)}")
