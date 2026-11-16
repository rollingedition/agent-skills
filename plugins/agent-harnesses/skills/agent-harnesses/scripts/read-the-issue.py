"""The issue the agent starts from, task T-01, and the case's files in sorted order. The model reads only the
issue and the system prompt, so these are what its first request holds about the task."""
from lib.case import CASE, case_files, load_tasks

task = load_tasks(only=["T-01"])[0]
print("task:", task.id)
print("issue:", task.issue)
files = case_files(CASE)
print("case files:", len(files))
for name in files:
    print(" ", name)
