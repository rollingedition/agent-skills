"""The five rubrics the book's judges use, each with the sha256 its recording's manifest holds, and how many lines its system
text has. The hash is the one lib.prompts.sha256_text gives for the system text and the user template together: each
recording's manifest was made from that pair, not from the system text alone, so the check compares the pair. The first
line of each rubric is printed to show which rubric it is; the full texts are in lib/prompts.py."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.prompts import (
    FAITH_SYSTEM, FAITH_TEMPLATE, HS2_SYSTEM, HS2_TEMPLATE, HS2B_SYSTEM, HS2B_TEMPLATE, PAIR_SYSTEM, PAIR_TEMPLATE,
    REF_SYSTEM, REF_TEMPLATE, sha256_text,
)
from lib.replay import ReplayModel

# (the rubric's name, the recording whose manifest holds its hash, its system text, its user template)
RUBRICS = (
    ("answer judge, reference-guided", "judge-answers-baseline", REF_SYSTEM, REF_TEMPLATE),
    ("HelpSteer2 calibration rubric, reference-free", "judge-helpsteer2", HS2_SYSTEM, HS2_TEMPLATE),
    ("HelpSteer2 rubric B, second wording", "judge-helpsteer2-rubric-b", HS2B_SYSTEM, HS2B_TEMPLATE),
    ("pairwise rubric", "judge-hs2-pairs-ab", PAIR_SYSTEM, PAIR_TEMPLATE),
    ("faithfulness rubric", "judge-faithfulness-baseline", FAITH_SYSTEM, FAITH_TEMPLATE),
)

for name, recording, system, template in RUBRICS:
    digest = sha256_text(system, template)
    # ReplayModel raises ValueError when the recording's manifest hash is not this one, so a match is checked, not assumed.
    ReplayModel(recording, digest)
    print(f"{name}: {len(system.splitlines())} lines")
    print(f"  sha256 of system text and template: {digest}")
    print(f"  first line: {system.splitlines()[0]}")
