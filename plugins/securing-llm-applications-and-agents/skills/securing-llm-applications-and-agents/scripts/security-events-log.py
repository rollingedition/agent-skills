"""The security log as sorted JSON lines, and the two queries an incident responder runs on the log alone.

The point rests on query 2: the undefended run's accepted fetches to outside hosts are in the log as `allow` lines, so
the log finds the incident, and the egress rule's log has none. The log has no times and no steps, so the same replies
always give the same lines. The log is printed, not stored: the examples never write into the book.
"""
import json
from collections import Counter

from lib import cases, defences, gate, replay, runs  # lib first: threads and seeds are fixed here

PRINTED = 5  # the first sorted lines are printed; the rest are counted


def logged() -> tuple[str, ...]:
    """The configurations the log covers: the undefended run, and each defence whose outbound calls or withheld results
    it records. A defence with no dev recording (rough-allowlist) cannot be replayed on the dev split. A deployed log
    holds only the configuration that ran."""
    return ("baseline",) + tuple(name for name, (label, _) in gate.DEFENCE_STANDARDS.items()
                                 if label in ("input", "harness") and (replay.RECORDED / f"{name}-dev").exists())


def main():
    tasks, attacks = cases.load_tasks("dev"), cases.load_cases("dev")
    names = logged()
    rows = [row for name in names for row in gate.security_events(name, *runs.replay_dev(name, tasks, attacks))]
    ordered = sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))  # the log's order, from the fields alone
    print(f"log lines: {len(ordered)}")
    for row in ordered[:PRINTED]:
        print(json.dumps(row, sort_keys=True))
    for (defence, decision), total in sorted(Counter((r["defence"], r["decision"]) for r in rows).items()):
        print(f"events, {defence}, {decision}: {total}")

    # Query 1: every refusal for one case, the first case in ID order that the egress rule refused.
    case = min(r["item"] for r in rows if r["defence"] == "egress-fetch" and r["decision"] == "refuse")
    refusals = [r for r in ordered if r["item"] == case and r["decision"] == "refuse"]
    print(f"query 1, case: {case}")
    print(f"query 1, refusals for the case: {len(refusals)}")
    for row in refusals:  # each refusal's defence, tool and reason, as logged
        print(f"query 1, refusal, {row['defence']}, {row['tool']}: {row['reason']}")

    # Query 2: every accepted fetch to a host outside the office's own, under two configurations, from the log alone.
    office = defences.office_hosts()
    for name in ("baseline", "egress-fetch"):
        outside = sorted((r["item"], r["host"]) for r in rows if r["defence"] == name and r["tool"] == "fetch_page"
                         and r["decision"] == "allow" and r["host"] not in office)
        print(f"query 2, fetches to an outside host, {name}: {len(outside)}")
        for case_id, host in outside:
            print(f"query 2, outside fetch, {name}, {case_id}: {host}")
    assert not any(r["defence"] == "egress-fetch" and r["tool"] == "fetch_page" and r["decision"] == "allow"
                   and r["host"] not in office for r in rows), "the egress rule let a fetch out"


if __name__ == "__main__":
    main()
