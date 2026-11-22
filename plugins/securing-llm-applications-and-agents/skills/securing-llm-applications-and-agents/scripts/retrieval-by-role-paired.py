"""Filtering search by the acting user's role before ranking: what it costs in benign tasks, and that on this set it removes no index attack, because none succeeded undefended.

The point rests on the count of benign tasks whose search lost a document the baseline's search had returned. The
paired difference in attack success is printed beside it, but on the index location the undefended attacks never
succeed here (loc-index is 0 of 13 on dev and 0 of 11 on held-out), so this run cannot show that the filter stops an
index attack. The per-location counts show where the defence acts. The held-out block is one run each, after the
defence was frozen on dev.
"""
from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

import re

DOC_ID = re.compile(r'"doc_id": "([^"]+)"')  # the search result is JSON text, which a long one may cut short
LOCATIONS = ("loc-upload", "loc-index")  # the locations the chapter's retrieval point is about
BLOCKS = (("dev", "baseline-dev", "retrieval-by-role-dev"), ("held-out", "baseline-held-out", "retrieval-by-role-held-out"))


def replay(split, recording, variant=None):
    """Utility, attack success and the document IDs each search returned, on one split, each keyed by ID."""
    tasks, attacks = cases.load_tasks(split), cases.load_cases(split)
    benign = runs.replay_tasks(recording, tasks, variant=variant)
    traces = runs.replay_cases(recording, attacks, variant=variant)
    utility = {t.id: int(scorers.utility(t, benign[t.id])) for t in tasks}
    success = {c.id: int(scorers.attack_success(c, traces[c.id])) for c in attacks}
    searched = {t.id: [i for e in benign[t.id].events if e.kind == "tool_result" and e.tool == "search_documents"
                       for i in DOC_ID.findall(e.result or "")] for t in tasks}
    return utility, success, searched


def main():
    for split, base_rec, role_rec in BLOCKS:
        base_u, base_s, base_docs = replay(split, base_rec)
        role_u, role_s, role_docs = replay(split, role_rec, variant="retrieval-by-role")
        benign_ids, case_ids = sorted(base_u), sorted(base_s)
        for name, util, succ in (("baseline", base_u, base_s), ("retrieval-by-role", role_u, role_s)):
            report.rate_lines(f"{split}, {name}, utility, {len(benign_ids)} benign tasks", [util[t] for t in benign_ids])
            report.rate_lines(f"{split}, {name}, attack success, {len(case_ids)} cases", [succ[c] for c in case_ids])
            for loc in LOCATIONS:  # the attack cases whose poisoned text sits in this location
                ids = sorted(c.id for c in cases.load_cases(split) if c.location == loc)
                report.rate_lines(f"{split}, {name}, attack success, {loc}, {len(ids)} cases", [succ[c] for c in ids])
        report.paired(f"{split}, utility, paired difference", [base_u[t] for t in benign_ids], [role_u[t] for t in benign_ids])
        report.paired(f"{split}, attack success, paired difference", [base_s[c] for c in case_ids], [role_s[c] for c in case_ids])

        # A benign task lost a document when the baseline's search returned one the role-filtered search did not.
        # Only tasks the baseline completed count: those are the ones whose search result they needed.
        lost = {t for t in benign_ids if base_u[t] and set(base_docs[t]) - set(role_docs[t])}
        dropped = {t for t in benign_ids if base_u[t] and not role_u[t]}  # the completed answers the defence cost
        print(f"{split}, benign tasks whose search lost a document they needed: {len(lost)} of {sum(base_u.values())}")
        print(f"{split}, benign tasks completed on the baseline and not on retrieval-by-role: {len(dropped)}")

        # The claims: every lost answer traces to a lost document, the role filter adds no attack success, and no index
        # attack succeeds under it.
        assert dropped == lost, "a utility drop with no lost document: the cause is not the search"
        assert not any(role_s[c] and not base_s[c] for c in case_ids), "the role filter made an attack succeed"
        assert all(role_s[c.id] == 0 for c in cases.load_cases(split) if c.location in LOCATIONS), "an index attack succeeded"


if __name__ == "__main__":
    main()
