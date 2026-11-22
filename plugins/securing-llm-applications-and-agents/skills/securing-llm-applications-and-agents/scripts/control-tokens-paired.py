"""The control-token fix on the 11-case control set (outside the frozen 120) and the 15 dev tasks, paired with the
baseline's parse. The line the prose rests on is `control set ... paired difference in attack success`, beneath its rates.
"""
from lib import cases, report, runs, scorers, tokens, variants  # lib first: threads and seeds are fixed here

MARKER = 151644  # the chat marker's id on the pinned tokenizer; main checks that it still is


def run_control(recording, variant):
    """Attack success by control case, the prompts by case, and utility by dev task, for one recording and its variant."""
    controls, benign = cases.load_control_cases(), cases.load_tasks("dev")
    assert (len(controls), len(benign)) == (11, 15), "the control set or the dev split has changed"
    model = runs.Capture(recording)
    traces = runs.replay_cases(recording, controls, variant=variant, model=model)
    tasks = runs.replay_tasks(recording, benign, variant=variant)
    success = {c.id: scorers.attack_success(c, traces[c.id]) for c in controls}
    return success, model.prompts, {t.id: scorers.utility(t, tasks[t.id]) for t in benign}


def main():
    assert tokens.ids("<|im_start|>") == [MARKER], "the chat marker's id has changed"
    on_s, on_p, on_u = run_control("ctrl-baseline-dev", "ctrl-baseline")  # special tokens parsed in the whole prompt
    off_s, off_p, off_u = run_control("ctrl-special-off-dev", "ctrl-special-off")  # parsed in trusted text only
    ids, dev = sorted(on_s), sorted(on_u)
    before, after = [on_s[c] for c in ids], [off_s[c] for c in ids]
    label = "control set (11 cases, outside the frozen 120)"
    report.rate_lines(f"{label}, attack success, special parsed", before)
    report.rate_lines(f"{label}, attack success, special off", after)
    report.paired(f"{label}, paired difference in attack success", before, after)
    util_on, util_off = [on_u[t] for t in dev], [off_u[t] for t in dev]
    report.rate_lines("utility, special parsed, 15 dev tasks", util_on)
    report.rate_lines("utility, special off, 15 dev tasks", util_off)
    report.paired("paired difference in utility, 15 dev tasks", util_on, util_off)
    # The count the point rests on: cases whose replayed prompt holds the marker in untrusted text, in each mode.
    on_mode = variants.VARIANTS["ctrl-baseline"].special_in_untrusted
    off_mode = variants.VARIANTS["ctrl-special-off"].special_in_untrusted
    reached_on = sum(any(runs.reached(p, on_mode, MARKER) for p in on_p[c]) for c in ids)
    reached_off = sum(any(runs.reached(p, off_mode, MARKER) for p in off_p[c]) for c in ids)
    print(f"control token reached the model, special parsed, {label}: {reached_on}")
    print(f"control token reached the model, special off, {label}: {reached_off}")
    assert reached_on > 0 and reached_off == 0, "the fix does not change what reaches the model"


if __name__ == "__main__":
    main()
