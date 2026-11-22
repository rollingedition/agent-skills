"""The exfiltration regressions for the chapter's security review (findings SEC7-01 to SEC7-05), with no model and no recording.

The 22 rows are in data/regressions/exfiltration.json. A render row runs the render policy on a reply, then renders the
output in each of the five views with markdown-it-py at the pin, and asserts that no URL a reader's browser loads or
follows points outside the office. A scan row asserts the labels the secret scanner gives. A trace row asserts that a
raw image the policy escaped leaves no render event in the sanitised trace.

Prints one verdict per attempt, sorted, by name only. Prints no phone numbers, keys or attack text.
"""
from lib import cases, regressions  # lib first: threads and seeds are fixed here


def main():
    regressions.report(regressions.check("exfiltration", cases.load_world()))


if __name__ == "__main__":
    main()
