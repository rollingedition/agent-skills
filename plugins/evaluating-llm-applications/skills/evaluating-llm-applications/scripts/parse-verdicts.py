"""What lib.contract.parse_verdict accepts and refuses: the verdict on a reply's first non-empty line, PASS or FAIL in capitals,
after optional emphasis marks. Each fixed reply below prints one line, the verdict or 'refused'. A refusal is not a FAIL:
the judge has not given a verdict, and the evaluation counts that as an error, not a failed answer."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import parse_verdict

CASES = (
    ("verdict first, PASS", "VERDICT: PASS\nReason: The answer matches the reference."),
    ("verdict first, FAIL", "VERDICT: FAIL\nReason: The answer gives a different version number."),
    ("emphasis around the line", "**VERDICT: FAIL**\nReason: The answer gives a different version number."),
    ("backticks around the line", "`VERDICT: PASS`\nReason: The answer matches the reference."),
    ("blank lines before the verdict", "\n\nVERDICT: PASS\nReason: The answer matches the reference."),
    ("no space after the colon", "VERDICT:PASS\nReason: The answer matches the reference."),
    ("two verdict lines, first one read", "VERDICT: FAIL\nVERDICT: PASS\nReason: Two verdicts."),
    ("lower case", "VERDICT: pass\nReason: The answer matches the reference."),
    ("title case", "Verdict: PASS\nReason: The answer matches the reference."),
    ("PARTIAL", "VERDICT: PARTIAL\nReason: Half of the answer matches."),
    ("verdict after a reason", "Reason: The answer matches the reference.\nVERDICT: PASS"),
    ("full stop after the verdict", "VERDICT: PASS.\nReason: The answer matches the reference."),
    ("words after the verdict", "VERDICT: PASS, mostly correct\nReason: The answer matches the reference."),
    ("bullet before the verdict", "- VERDICT: PASS\nReason: The answer matches the reference."),
    ("pairwise letter", "VERDICT: A\nReason: Response A is better."),
    ("bare word", "PASS\nReason: The answer matches the reference."),
    ("empty reply", ""),
    ("blank lines only", "  \n\n   "),
)

for label, raw in CASES:
    verdict = parse_verdict(raw)
    print(f"{label}: {verdict if verdict is not None else 'refused'}")
