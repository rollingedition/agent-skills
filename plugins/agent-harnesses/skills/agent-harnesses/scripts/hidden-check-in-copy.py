"""The hidden check runs in a fresh folder that holds only the agent's package and README, plus the hidden file. A planted
conftest.py in the agent's copy does not come along, and the case library is unchanged after the check. The folder is
built by copy_package before the hidden file is added, so the count is the package and README alone."""
import shutil
import tempfile
from pathlib import Path

from lib.case import CASE, DATA, load_tasks, scratch_copy
from lib.tasks import copy_package, hidden_check_passes, snapshot

task = load_tasks(only=["T-04"])[0]
before = snapshot(CASE, ".")
case_passes = hidden_check_passes(task, CASE)
print("case without the fix, hidden check passes:", case_passes)
assert not case_passes

scratch = scratch_copy(CASE)
fresh = Path(tempfile.mkdtemp(prefix="check-folder-"))
try:
    shutil.copy(DATA / "solutions" / "T-04" / "unitcraft" / "units.py", scratch / "unitcraft" / "units.py")
    (scratch / "conftest.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    print("agent copy with the fix, hidden check passes:", hidden_check_passes(task, scratch))
    copy_package(scratch, fresh)
    names = sorted(p.relative_to(fresh).as_posix() for p in fresh.rglob("*") if p.is_file())
    print("package and README files in the check's folder:", len(names))
    print("only the package and README came along:", all(n.startswith("unitcraft/") or n == "README.md" for n in names))
    print("the hidden file is added beside them:", task.check)
    assert hidden_check_passes(task, scratch) and "conftest.py" not in names
finally:
    shutil.rmtree(scratch, ignore_errors=True)
    shutil.rmtree(fresh, ignore_errors=True)

print("case library unchanged:", snapshot(CASE, ".") == before)
assert snapshot(CASE, ".") == before
