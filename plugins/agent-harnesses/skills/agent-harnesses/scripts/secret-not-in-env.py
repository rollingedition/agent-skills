"""A secret in the harness's environment never reaches the command, because the command's environment is built from an
allowlist. The example sets a fake key in its own environment, as a real key is set when the harness starts, runs a
command that lists the names it can see, and checks the names and the output. It does not test reads of the harness's
environment through /proc: whether those succeed depends on the kernel, so the chapter says that instead."""
import ast
import os
import sys

from lib.sandbox import run_sandboxed, scratch_dir
from lib.tools import ENV_KEEP

SECRET, VALUE = "FAKE_API_KEY", "fake-value-for-the-example"
os.environ[SECRET] = VALUE  # the harness's own environment holds the key; the command must not inherit it
COMMAND = "import os\nprint(sorted(os.environ))\n"
# The interpreter adds LC_CTYPE itself when the locale is C (PEP 538); the harness does not set it.
ALLOWED_NAMES = set(ENV_KEEP) | {"HOME", "PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "LC_CTYPE"}

with scratch_dir() as work:
    result = run_sandboxed([sys.executable, "-c", COMMAND], cwd=work, timeout=30)
names = ast.literal_eval(result.out.strip().splitlines()[0])  # the command prints one list of names
print("secret name in the command's environment:", sum(SECRET in n for n in names))
print("secret value in the output the model would see:", result.out.count(VALUE))
print("names outside the allowlist:", len(set(names) - ALLOWED_NAMES))
assert SECRET not in names and VALUE not in result.out and set(names) <= ALLOWED_NAMES
