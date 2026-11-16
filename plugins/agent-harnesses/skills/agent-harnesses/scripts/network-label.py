"""The network label must agree with what a command reaches. A listener on this host's loopback is reachable only when
the command has no network namespace. The printed line is the same on every runtime, because the checks are assertions:
the label and the reach must agree, and the command must have run. No external network is used."""
import socket
import sys

from lib.sandbox import NAMESPACE, NoNetworkBlock, network_label, run_sandboxed, scratch_dir

CLIENT = (
    "import socket\n"
    "try:\n"
    "    socket.create_connection(('127.0.0.1', {port}), timeout=5).close()\n"
    "    print('reached')\n"
    "except OSError:\n"
    "    print('blocked')\n"
)

with socket.socket() as listener, scratch_dir() as work:
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    code = CLIENT.format(port=listener.getsockname()[1])
    label = network_label()
    asked = 1
    result = run_sandboxed([sys.executable, "-c", code], cwd=work, timeout=30)
    asked += 1
    try:
        run_sandboxed([sys.executable, "-c", code], cwd=work, timeout=30, require_network_block=True)
        blocked_refused = False
    except NoNetworkBlock:
        blocked_refused = True
reached = result.out.strip() == "reached"
assert not result.timed_out and result.out.strip() in ("reached", "blocked")  # a run cut short proves nothing
assert (label == NAMESPACE) == (not reached)  # the label names a namespace only when the command could not reach the host
assert blocked_refused == (label != NAMESPACE)  # the block refuses to run exactly when no namespace is made
print("commands the example asked to run:", asked)
