"""A child that calls setsid() leaves the process group, so the group kill misses it. Without a PID namespace the child
outlives the sandbox, and the example checks that. The first run shows that a child holding the output pipe cannot keep
the sandbox waiting past its time limit. The example does not check the case with a PID namespace: whether the kernel
grants one depends on the machine, and the printed lines and checks must hold on every machine."""
import os
import sys

from lib.sandbox import escape_survives, run_sandboxed, scratch_dir

HOLDER = (  # the child waits on the pipe the example closes after the run, and so keeps the output pipe open
    "import subprocess, sys, time\n"
    "subprocess.Popen([sys.executable, '-c', 'import sys; sys.stdin.read()'], stdin=int(sys.argv[1]), start_new_session=True)\n"
    "time.sleep(60)\n"
)

with scratch_dir() as work:
    ctl_r, ctl_w = os.pipe()
    try:
        held = run_sandboxed([sys.executable, "-c", HOLDER, str(ctl_r)], cwd=work, timeout=2, pass_fds=(ctl_r,),
                             isolate_pids=False)
    finally:
        os.close(ctl_w)  # releases the held child
        os.close(ctl_r)
    without = escape_survives(work, isolate_pids=False)
print("commands stopped at the time limit:", int(held.timed_out))
print("setsid children alive after the sandbox returned, without a PID namespace:", int(without))
assert held.timed_out and held.out == ""
assert without is True
