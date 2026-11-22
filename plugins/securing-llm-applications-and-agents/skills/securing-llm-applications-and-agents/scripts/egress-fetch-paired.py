"""The outbound allowlist plus the fetch query rule, against the undefended run, on the 15 benign tasks and 60 cases of each split: dev, then held-out.

The chapter's claim rests on the paired difference in attack success, egress minus baseline, with its interval.
The refusals are counted by the rule that made them, read from each trace's defence events.
"""
from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

# The query rule's refusal reasons begin with these; every other refusal is the allowlist's.
QUERY_RULE = ("fetch_page: the URL carries a tenant's record", "fetch_page: the URL could not be checked")

# Each split with its undefended recording and its run under the rule, both as recorded.
SPLITS = (("dev", "baseline-dev", "egress-fetch-dev"), ("held-out", "baseline-held-out", "egress-fetch-held-out"))


def main():
    for split, base_rec, eg_rec in SPLITS:
        tasks = sorted(cases.load_tasks(split), key=lambda t: t.id)  # the 15 benign tasks of the split
        attacks = sorted(cases.load_cases(split), key=lambda c: c.id)  # the 60 attack cases of the split
        nt, na = f"{len(tasks)} {split} benign tasks", f"{len(attacks)} {split} cases"

        # The undefended run and the run under the rule, each replayed from its own recording.
        base_benign = runs.replay_tasks(base_rec, tasks)
        base_attacks = runs.replay_cases(base_rec, attacks)
        eg_benign = runs.replay_tasks(eg_rec, tasks, variant="egress-fetch")  # hooks built per task, as recorded
        eg_attacks = runs.replay_cases(eg_rec, attacks, variant="egress-fetch")

        base_util = [scorers.utility(t, base_benign[t.id]) for t in tasks]
        eg_util = [scorers.utility(t, eg_benign[t.id]) for t in tasks]
        base_succ = [scorers.attack_success(c, base_attacks[c.id]) for c in attacks]
        eg_succ = [scorers.attack_success(c, eg_attacks[c.id]) for c in attacks]

        report.rate_lines(f"utility, baseline, {nt}", base_util)
        report.rate_lines(f"utility, egress-fetch, {nt}", eg_util)
        report.rate_lines(f"attack success, baseline, {na}", base_succ)
        report.rate_lines(f"attack success, egress-fetch, {na}", eg_succ)
        report.paired(f"paired difference in utility, egress minus baseline, {split}", base_util, eg_util)
        report.paired(f"paired difference in attack success, egress minus baseline, {split}", base_succ, eg_succ)
        report.newly_lines(f"attack success stopped by the rule, {split}", f"attack success added by the rule, {split}",
                           base_succ, eg_succ)

        # Refusals by rule, benign runs and attack runs apart; a rule that refused nothing still prints a line.
        for group, traces in (("benign", eg_benign.values()), ("attack", eg_attacks.values())):
            rule = [("query rule" if str(e.result["reason"]).startswith(QUERY_RULE) else "allowlist")
                    for t in traces for e in t.events if e.kind == "defence" and e.result.get("blocked")]
            for name in ("allowlist", "query rule"):
                print(f"refusals by {name}, {group} runs, {split}: {rule.count(name)}")

        # A design guarantee the prose relies on: the rule adds no attack success on this split.
        assert all(b or not e for b, e in zip(base_succ, eg_succ)), f"the rule added an attack success on {split}"


if __name__ == "__main__":
    main()
