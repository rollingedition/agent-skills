"""The tokens each variant adds to the prompts it is given, on the 15 dev benign tasks, summed over each task's model
calls. Each variant also prints the part of that sum that falls on the tool definitions, the rest of it, and the number
of model calls its run made, because a run that makes fewer calls has fewer prompts to add to. The line the prose rests
on is `prompt-encode, added prompt tokens in tool definitions, median`, beside its total. The tokens are counted with
lib/tokens.py on the pinned Qwen3-0.6B tokenizer, which matches the 4B model's count on the baseline prompts (notes/probes.md, P-1).
"""
import statistics

from lib import cases, defences, harness, replay, runs, tokens, tools  # lib first: threads and seeds are fixed here

VARIANTS = {"prompt-datamark": defences.prompt_datamark, "prompt-delimiters": defences.prompt_delimiters,
            "prompt-encode": defences.prompt_encode, "prompt-repeat": defences.prompt_repeat,
            "prompt-warning": defences.prompt_warning}


def added_tokens(recording, defence, world, tasks):
    """Per task ID: the tokens the defence added to the prompts the model was given, summed over its model calls; the
    part of that sum on the tool definitions; and the number of model calls."""
    model = replay.ReplayModel(recording)  # the variant's own recording, so each reply is the one it was given
    totals = {}
    for task in tasks:
        growths = []  # per call: the growth of the whole prompt, and of its tool definitions

        def transform(segments):  # the hook sees each prompt before the change, so the growth is the defence's own
            changed = defence(segments)
            growths.append(tokens.growth(segments, changed, harness.prompt_text))
            return changed

        hooks = harness.Hooks(name="measure", transform_input=transform)
        system = harness.system_text(runs.TEMPLATE, task.acting_user, world)
        harness.run_episode(task.id, task.text, task.acting_user, model, system=system,
                            state=tools.ToolState.new(task.acting_user), hooks=hooks,
                            assistant_prefix=harness.ASSISTANT, max_tokens=runs.ANSWER_TOKENS)
        totals[task.id] = tokens.sum_growth(growths)
    return totals


def main():
    world, tasks = cases.load_world(), cases.load_tasks("dev")
    assert len(tasks) == 15, "the dev benign tasks have changed"
    for name in sorted(VARIANTS):
        totals = added_tokens(f"{name}-dev", VARIANTS[name], world, tasks)
        added, schemas, elsewhere, calls = tokens.columns(totals)  # sorted by task ID, so the order is fixed
        print(f"{name}, added prompt tokens, median: {statistics.median(added):.0f}")
        print(f"{name}, added prompt tokens, maximum: {max(added)}")
        print(f"{name}, added prompt tokens in tool definitions, median: {statistics.median(schemas):.0f}")
        print(f"{name}, added prompt tokens elsewhere, median: {statistics.median(elsewhere):.0f}")
        print(f"{name}, model calls, median: {statistics.median(calls):.0f}")


if __name__ == "__main__":
    main()
