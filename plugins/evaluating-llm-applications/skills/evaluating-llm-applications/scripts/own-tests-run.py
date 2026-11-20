"""Runs the book's own tests, lib/tests, in this process and prints how many passed and failed in each module, then pytest's
exit code. Exit code 0 means every test was collected and passed. Exit code 5 means nothing was collected, so the example
prints the code it got rather than a silent pass. No paths and no timings are printed: they vary from run to run."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from collections import Counter
from pathlib import Path

import pytest

TESTS = Path(lib.__file__).resolve().parent / "tests"  # read here, never printed


class Outcomes:
    """Counts each test's outcome by module. A failed setup or teardown counts as a failure of its test."""

    def __init__(self) -> None:
        self.passed = Counter()
        self.failed = Counter()

    def pytest_runtest_logreport(self, report) -> None:
        # The node id starts with the file's path; keep only the module's name, so no path is printed.
        module = Path(report.nodeid.split("::")[0]).stem
        if report.when == "call" and report.passed:
            self.passed[module] += 1
        elif report.failed:
            self.failed[module] += 1


collector = Outcomes()
# -p no:terminal turns off pytest's own printing, which carries timings. That also removes the -q option, which belongs to
# the terminal reporter, so it is not passed. -p no:cacheprovider keeps .pytest_cache out of the working copy.
exit_code = pytest.main(
    [str(TESTS), "-p", "no:terminal", "-p", "no:cacheprovider"],
    plugins=[collector],
)

modules = sorted(path.stem for path in TESTS.glob("test_*.py"))  # every module, even one with no failures
print("tests by module (passed, failed):")
for module in modules:
    print(f"  {module}: {collector.passed[module]} passed, {collector.failed[module]} failed")
print(f"total: {sum(collector.passed.values())} passed, {sum(collector.failed.values())} failed")
print(f"pytest exit code: {int(exit_code)}")
