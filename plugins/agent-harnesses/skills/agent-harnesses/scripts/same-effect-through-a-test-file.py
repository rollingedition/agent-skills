"""A test file can do what the refused command did. The copy's conftest.py removes tests/ when pytest loads it. Run as
the allowlist lists it, pytest loads the conftest and the folder goes. Run as the harness runs it (hardened: the config
is the harness's, and conftest files are skipped), the folder stays. The harness's run passes require_network_block=False,
so the example runs on a machine with no namespace; the network is not what this example shows. The copy is temporary;
nothing real is touched."""
from lib.sandbox import allowed_argv, run_allowed, run_sandboxed, scratch_dir

CONFTEST = "import shutil\nshutil.rmtree('tests', ignore_errors=True)\n"
COMMAND = "python -m pytest -q -p no:cacheprovider"

with scratch_dir() as listed, scratch_dir() as hardened:
    for work in (listed, hardened):
        (work / "conftest.py").write_text(CONFTEST)
    run_sandboxed(allowed_argv(COMMAND), cwd=listed, timeout=60)
    reply = run_allowed(COMMAND, cwd=hardened, require_network_block=False)
    print("test folders left after the listed command:", int((listed / "tests").is_dir()))
    print("test folders left after the harness's run:", int((hardened / "tests").is_dir()))
    assert not (listed / "tests").is_dir() and (hardened / "tests").is_dir()
    assert reply.startswith("exit:")
