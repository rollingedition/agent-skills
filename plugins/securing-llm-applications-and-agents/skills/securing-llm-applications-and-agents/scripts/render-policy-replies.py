"""The render policy over the final reply of every attack case, undefended, on the dev and the held-out splits.

The chapter's claim rests on the attack success line before and after sanitising, for each split. Most replies on
this set carry no image or link, so the policy changes few of them; that count is printed beside the rates.
"""
from lib import cases, defences, egress, report, runs, scorers  # lib first: threads and seeds are fixed here

# The undefended baseline recording for each split: the replies the assistant gave with no defence on.
RECORDINGS = {"dev": "baseline-dev", "held-out": "baseline-held-out"}


def main():
    world = cases.load_world()
    hosts = defences.office_hosts()  # the office's own hostnames, from the fixture pages

    for split, recording in RECORDINGS.items():
        attacks = sorted(cases.load_cases(split), key=lambda c: c.id)
        traces = runs.replay_cases(recording, attacks)

        before, after = [], []
        removed_total = 0
        changed = []  # cases whose rendered image URLs differ after the policy
        carried = 0   # cases whose reply holds an image or a link at all
        for case in attacks:
            trace = traces[case.id]
            clean_trace, removed = egress.sanitised_trace(trace, hosts, world)  # the policy on the final reply
            before.append(scorers.attack_success(case, trace))
            after.append(scorers.attack_success(case, clean_trace))
            removed_total += len(removed)
            if scorers.rendered_urls(trace.reply) != scorers.rendered_urls(clean_trace.reply):
                changed.append(case.id)
            # A reply with no image or link has nothing for the policy to act on.
            if scorers.rendered_urls(trace.reply) or scorers.link_urls(trace.reply):
                carried += 1

        report.rate_lines(f"attack success before sanitising, {split}, {len(attacks)} cases", before)
        report.rate_lines(f"attack success after sanitising, {split}, {len(attacks)} cases", after)
        report.newly_lines(f"attack success removed by sanitising, {split}",
                           f"attack success added by sanitising, {split}", before, after)
        print(f"URLs removed, {split}: {removed_total}")
        print(f"cases whose rendered URLs changed, {split}: {len(changed)}")
        print(f"cases whose rendered URLs changed, {split}, IDs: {', '.join(changed) or 'none'}")
        print(f"attack cases whose reply had any image or link, {split}: {carried} of {len(attacks)}")

        # Sanitising only removes what a reader would load or follow, so it cannot create an attack success.
        assert all(b or not a for b, a in zip(before, after)), f"sanitising added an attack success, {split}"


if __name__ == "__main__":
    main()
