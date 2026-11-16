"""The allowlist decides on the parsed argv, before anything runs. Only the test command is listed; refused commands never
start. No tool in this book offers the model a command tool, so this is the check a command tool would use; the
harness's own test run builds its argv directly. The allowlist picks the program, not the code it runs: that is what
the next example's replay shows."""
import inspect

from lib.sandbox import Refused, allowed_argv, run_sandboxed

COMMANDS = (
    "python -m pytest -q -p no:cacheprovider",
    "python   -m pytest -q  -p no:cacheprovider",
    "python -m pytest -q -p no:cacheprovider --collect-only",
    "pytest -q -p no:cacheprovider",
    "rm -rf tests",
    "python -m pytest -q -p no:cacheprovider; rm -rf tests",
    "sh -c 'rm -rf tests'",
    "python -c 'print(1)'",
    "python -m pytest -q 'unclosed",
)
allowed, refused = [], []
for command in COMMANDS:
    try:
        allowed_argv(command)
        allowed.append(command)
        print("allowed:", repr(command))
    except Refused as reason:
        refused.append(command)
        print("refused:", reason)
print("allowed commands:", len(allowed))
print("refused commands:", len(refused))
assert len(allowed) == 2 and len(refused) == len(COMMANDS) - 2
assert "shell" not in inspect.signature(run_sandboxed).parameters
