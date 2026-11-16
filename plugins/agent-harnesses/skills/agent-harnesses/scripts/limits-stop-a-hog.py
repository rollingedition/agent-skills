"""What the limits stop, each with its own cap. A memory hog and a file writer exit non-zero at their caps; a sleeper is
stopped at the time limit. The grandchild checks run without a PID namespace, so their answers hold on any kernel: a
kill of the direct child leaves a grandchild in the group alive, and the group kill removes it. The caps are per
process, not per command (see the sandbox module)."""
import sys

from lib.sandbox import grandchild_survives, run_sandboxed, scratch_dir

HOG = "x = bytearray(600 << 20)\nprint('allocated')"
WRITER = "open('big', 'wb').write(b'x' * (2 << 20))\nprint('written')"

with scratch_dir() as work:
    sleeper = run_sandboxed([sys.executable, "-c", "import time; time.sleep(30)"], cwd=work, timeout=5)
    hog = run_sandboxed([sys.executable, "-c", HOG], cwd=work, timeout=10, memory=256 << 20)
    writer = run_sandboxed([sys.executable, "-c", WRITER], cwd=work, timeout=10, file_size=1 << 20)
    before = grandchild_survives(work, group_kill=False, isolate_pids=False)
    after = grandchild_survives(work, group_kill=True, isolate_pids=False)
    stopped = [sleeper, hog, writer]
    print("commands stopped at the time limit:", sum(r.timed_out for r in stopped))
    print("commands that exited non-zero at a cap:", sum(r.code not in (0, None) for r in stopped[1:]))
    print("lines printed after a cap was hit:", sum(w in r.out for r, w in ((hog, "allocated"), (writer, "written"))))
    print("grandchildren alive after the direct child was killed:", int(before))
    print("grandchildren alive after the group kill:", int(after))
    assert sleeper.timed_out and not hog.timed_out and not writer.timed_out
    assert hog.code not in (0, None) and writer.code not in (0, None)
    assert "allocated" not in hog.out and "written" not in writer.out
    assert before is True and after is False
