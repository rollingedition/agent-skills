---
title: "Evaluating LLM Applications"
chapter: "Read the replies to find what to measure"
chapter_id: read-the-outputs
book: evaluating-llm-applications
edition: 2026.11.3
verified: 2026-11-21
edition_code: 4V0Y-VKTV
canonical: https://rollingedition.com/evaluating-llm-applications/read-the-outputs
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Read the replies to find what to measure,” chapter 2 of Evaluating LLM Applications, Edition 2026.11.3, examples passed Nov 21, 2026. By Rolling Edition, https://rollingedition.com/evaluating-llm-applications/read-the-outputs. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Read the replies to find what to measure

By the end of this chapter you can read a set of replies from an assistant, sort what is wrong with each one into a failure mode, and say which of those failures a check can see.

Chapter 1 ended on a limit: twenty items can find broken answers, but they can't rank two prompts. The assistant in this book answers from three versions of sablefile's docs, 1.0, 1.1 and 2.0, and a question about one version can get an answer that is right for another. A pass rate counts every such failure the same way and names none of them. A team that measures only with a pass rate therefore writes its checks for the failures it expects, and the failures it doesn't expect go unchecked. Reading the replies first is how you find the second kind. Chapter 1's interval says how far a score can be trusted. This chapter asks what each variant gets wrong, which a score can't say.

Reading before counting has support outside this book. [Chapter 1](measure-before-you-change) cited Shankar and colleagues' [*Who Validates the Validators?*](https://arxiv.org/abs/2404.12272) (2024) for the point that people refine their grading criteria while they grade outputs. That paper is mainly a system, EvalGen, and its user study of nine practitioners is the part this chapter relies on. The drift the study records happened while people graded outputs. That a change to the pipeline can make the criteria drift is the authors' discussion, not a finding of the study. It is one study, so this chapter treats it as a caution, not as a result the book measures.

This chapter uses the 80 dev items, the split of the test set this book works with while it develops its measures. It reads only the dev items, so nothing here is tuned to the held-out items, and the held-out decline counts appear in [chapter 10](declining-when-the-docs-dont-say). The reading produces three things: a note on each reply, a count of the defects those notes fall into, and a candidate check for each defect. Every reply here is a recording made once for each variant and replayed by the examples, so the reading is the same on every run. Quotes of replies come from the recorded outputs, and the reference answers are printed beside their items, so any line the prose quotes from them can be found in the example's output. The notes sit in a data file that the tally example reads.

Throughout, a reply counts as right when it gives the reference answer, or when it declines because the reference says the docs don't say. Its citations are checked on their own, by the citation check in [chapter 1](measure-before-you-change#citations-in-code) and the checks in [chapter 4](checks-in-code). Anything else is a failure, and the rest of the chapter says which kind. The same steps work on a replay file of your own. Group its replies by kind, read each one against its reference, code each by its main defect, and write one candidate check per mode. This chapter does that for the sablefile replies, so you can follow each step on data you can open.

This chapter doesn't choose the checks or write a judge's rubric, and it doesn't estimate how often each mode happens in real use. Those come in later chapters, and each one relies on the modes named here.

## What the replies look like {#what-the-replies-look-like}

Three variants of the assistant answered the same dev items, and every comparison in this chapter sets one variant's replies beside another's. The baseline is the setup chapter 1 measured. It retrieves sections only from the version the question asks about, so its context holds one version's docs. The unfiltered variant drops the baseline's version filter. Its context can hold sections from all three versions, each marked with its version, so the model can see a mismatch and can also copy the wrong version's text. The second-model variant keeps the baseline's prompt and hands the answer to a smaller model, Qwen3 with 0.6 billion parameters in an 8-bit build. The prompt is the same, so a difference from the baseline comes from the model, not the prompt.

Each dev item has a kind, and the kind says what a right reply looks like. An [answerable item](#the-twenty-items) is one the docs answer. An [unanswerable item](#the-twenty-items) asks for something the docs don't say, and the right reply is a decline in the words the assistant was given: "The docs don't say." A version-dependent item has an answer that changes with the version asked about, so the same question asked of two versions can have two right answers. An ambiguous item can be read two ways, and the docs answer each reading. Some items are [planted](#the-twenty-items), written to catch one specific mistake. The output gives each planted item its reason, which is one of a false premise, a near-miss term, a version swap, a stale answer or an ambiguous target. A reply that fails a planted item shows whether the assistant made the mistake that item was written for.

Reading one item takes three steps. Start with the question and its version, since a reply is right only for the version it names. Then read the reference answer, which is the author's statement of what a right reply says. Then read the three replies against it, one at a time. Only after that does a reader group the replies or count them.

The example that follows is where the chapter starts. It prints every dev item with its reference answer and each variant's reply, grouped by kind and sorted by ID, so the three replies to one question sit on adjacent lines. Read across an item's lines, not down one variant's column. The variants fail in different ways on the same question, and that difference is what to see. Each reply is cut to its first 120 characters, and its line says whether the reply declined and what it cited. A reply that holds the decline phrase inside other text is marked as a phrase, not a decline, so you can see where the parser draws the line.

Example `read-replies-dev` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.3:

```python
"""Prints the dev items, grouped by kind and sorted by ID, with each item's reference answer and the baseline,
unfiltered and second-model replies.

The reference is printed in full under its item, since the reading compares each reply with it. Each reply is one line:
whether it declined, its citations, and its first 120 characters. The reader's job is to set these side by side and
see which failure each reply shows (the codes are in data/failure-codes.json)."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.contract import DECLINE, parse_reply
from lib.prompts import P1_SHA256
from lib.replay import ReplayModel
from lib.testset import load_items

RECORDINGS = {  # the three variants, in the order the chapter discusses them
    "baseline": "assistant-baseline",
    "unfiltered": "assistant-unfiltered",
    "second-model": "assistant-second-model",
}
KINDS = ("answerable", "unanswerable", "version-dependent", "ambiguous")  # plan section 3.1 order
SHOWN = 120  # characters of each reply printed; the full text is in the recording

# The prompt hash is checked here, so a recording made from another prompt fails to load.
models = {name: ReplayModel(recording, P1_SHA256) for name, recording in RECORDINGS.items()}
items = load_items(split="dev")  # dev only: the held-out items are not read in this chapter (plan section 3.4)

for kind in KINDS:
    group = [item for item in items if item.kind == kind]  # load_items already sorts by ID
    print(f"## {kind}: {len(group)} dev items")
    for item in group:
        planted = f"planted ({item.planted_why})" if item.planted else "not planted"
        print(f"{item.id} | version {item.version} | {planted} | {item.question}")
        reference = item.reference_answer or "none: the item is unanswerable, so the right reply declines"
        print(f"  reference: {reference}")
        for name in RECORDINGS:
            reply = parse_reply(models[name].reply(item.id, 0))
            if reply.declined:
                mark = "declined"
            elif DECLINE in reply.text:
                # The phrase is there, but with other text: the parser does not call that a decline.
                mark = "decline phrase with other text"
            else:
                mark = f"cites {' '.join(reply.citations)}" if reply.citations else "no citation"
            text = reply.text.replace("\n", " ")  # a reply may hold line breaks; one line keeps the output readable
            more = "..." if len(text) > SHOWN else ""
            print(f"  {name} ({mark}): {text[:SHOWN]}{more}")
```

Output:

```text
## answerable: 40 dev items
q-0005 | version 2.0 | planted (near-miss-term) | Does sablefile 2.0 still read sablefile.lock in my project root?
  reference: Only as a fallback. If the new file is missing and an old sablefile.lock is present, a 2.0 command reads the old file but warns you about it. Once the new file exists, 2.0 reads only that one, and sablefile never deletes the old file.
  baseline (cites install-upgrade): No, sablefile 2.0 does not read `sablefile.lock` in the project root. Version 2.0 moves the lock file to a new place. Th...
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0006 | version 2.0 | not planted | Is there a way to make check exit with status 0 even when a file has drifted in 2.0?
  reference: Yes. Pass --no-fail to check. It still prints each DRIFT line, but it exits with status 0, so a script can report drift without failing. The flag changes nothing except the exit status.
  baseline (cites no-fail-flag): Yes, there is a way to make `check` exit with status 0 even when a file has drifted in 2.0. Use the `--no-fail` flag wit...
  unfiltered (cites no-fail-flag): Yes, there is a way to make `check` exit with status 0 even when a file has drifted in version 2.0. Use the `--no-fail` ...
  second-model (cites no-fail-flag): The `--no-fail` flag is used to make the check exit with status 0 even when files have drifted. [sec:no-fail-flag]
q-0007 | version 1.1 | not planted | In 1.1, will an ignore entry of docs/**/*.tmp catch a file two folders down, like docs/x/y/a.tmp?
  reference: Yes. Version 1.1 adds the double-star pattern, which matches zero or more folders. So docs/**/*.tmp matches docs/x/y/a.tmp as well as files directly in docs.
  baseline (cites ignore-recursive): Yes, an ignore entry of `docs/**/*.tmp` will catch a file two folders down, like `docs/x/y/a.tmp`. [sec:ignore-recursive...
  unfiltered (cites ignore-recursive): Yes, in version 1.1, an ignore entry of `docs/**/*.tmp` will catch a file two folders down, like `docs/x/y/a.tmp`. [sec:...
  second-model (no citation): The docs section does not allow for an ignore entry of docs/**/*.tmp to catch a file two folders down, as per the rules....
q-0008 | version 2.0 | not planted | In 2.0, is there a way to re-include something that an earlier ignore line had excluded?
  reference: Yes, with a leading exclamation mark. A line that starts with ! negates an earlier match, so a later line can restore a file that an earlier line ignored.
  baseline (cites ignore-syntax): Yes, in 2.0, you can re-include something that an earlier ignore line had excluded by using a leading `!` to negate an e...
  unfiltered (cites ignore-syntax): Yes, in version 2.0, you can re-include something that an earlier ignore line had excluded by using a leading `!` to neg...
  second-model (declined): The docs don't say.
q-0009 | version 1.0 | not planted | What does one line of the 1.0 lock file hold?
  reference: The SHA-256 hash of a generated file's content, then two spaces, then that file's path. The 1.0 lock has no mode field.
  baseline (cites lockfile): One line of the 1.0 lock file holds the SHA-256 hash of the file's content, two spaces, then the path. [sec:lockfile]
  unfiltered (cites lockfile): One line of the 1.0 lock file holds the SHA-256 hash of the file's content, then the file's mode, then the path. [sec:lo...
  second-model (cites lockfile): The lock file holds the SHA-256 hash of the file's content, two spaces, and the path. [sec:lockfile]
q-0010 | version 2.0 | not planted | Will syncing the same content twice in 2.0 produce a different lock file each time?
  reference: No. The 2.0 lock file is JSON with no timestamps, so the same content always gives back an identical file.
  baseline (cites lockfile): No, syncing the same content twice in 2.0 will not produce a different lock file each time. The lock file has no timesta...
  unfiltered (cites lockfile): No, syncing the same content twice in 2.0 will produce an identical lock file each time because the lock file has no tim...
  second-model (declined): The docs don't say.
q-0011 | version 1.1 | not planted | How many times does 1.1 retry a remote template fetch that keeps failing, and can a flag change that?
  reference: Five times, before the command gives up. In 1.1 that number is fixed, and no flag or setting can change it.
  baseline (cites remote-retries): The count is fixed in 1.1, and no flag or setting changes it. [sec:remote-retries]
  unfiltered (cites remote-retries): In version 1.1, sablefile retries a remote template fetch up to 5 times before giving up. The count is fixed and no flag...
  second-model (cites remote-retries): The count is fixed in 1.1, and no flag or setting changes it. [sec:remote-retries]
q-0012 | version 2.0 | not planted | I want sync to retry a slow remote template only twice in 2.0. What do I pass?
  reference: Pass --retries 2 to sync. The flag sets how many times a failed fetch is retried, in place of the default of five, and it only affects the command it is given to.
  baseline (cites retries-flag): Pass `--retries 2` to sync. [sec:retries-flag]
  unfiltered (cites retries-flag): Pass `--retries 2` to sync. [sec:retries-flag]
  second-model (cites retries-flag): `--retries 2` to pass. [sec:retries-flag]
q-0013 | version 1.0 | not planted | In 1.0, which table in sablefile.toml holds the values a placeholder can name?
  reference: The [values] table. Each name in it can be used as a placeholder, and a placeholder name in a template must match a key in that table.
  baseline (cites config-values): The `[values]` table holds the values a placeholder can name. [sec:config-values]
  unfiltered (cites config-values): The `[values]` table in sablefile.toml holds the values a placeholder can name. [sec:config-values]
  second-model (cites config-values): The values table holds the values a placeholder can name. [sec:config-values]
q-0014 | version 1.1 | not planted | What does sablefile init put into a new sablefile.toml in 1.1?
  reference: A [values] table with one entry, project, set to the folder's name, and no [[file]] tables. init writes no other file.
  baseline (cites init-command): `sablefile init` creates `sablefile.toml` in the folder where you run it, or in the folder you name. The new file has a ...
  unfiltered (cites init-command): `sablefile init` creates `sablefile.toml` in the folder where you run it, or in the folder you name. The new file has a ...
  second-model (declined): The docs don't say.
q-0051 | version 2.0 | planted (near-miss-term) | My 1.x ignore file uses shell globs, so does *.log only match files in the top folder in 2.0?
  reference: No. Shell glob rules no longer apply in 2.0. Entries use gitignore syntax, so *.log matches at any depth, and a trailing slash limits an entry to directories.
  baseline (cites ignore-syntax): In 2.0, entries use gitignore syntax. A line such as `*.log` matches at any depth. Therefore, `*.log` matches files in a...
  unfiltered (cites ignore-syntax): No, in 2.0, `*.log` matches at any depth, not just in the top folder. [sec:ignore-syntax]
  second-model (declined): The docs don't say.
q-0052 | version 2.0 | planted (near-miss-term) | I have {{project}} all through my templates from 1.x. Is that still valid in 2.0?
  reference: No. In 2.0 each placeholder is written as a dollar sign and braces, ${project}. The double-brace form is an error: rendering fails, sync reports the file and line, and it exits with status 1.
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0053 | version 2.0 | planted (stale-answer) | I have an old sablefile.lock from 1.1. When I first run sync --apply under 2.0, what happens to it?
  reference: 2.0 writes a new .sablefile/lock.json holding each file's hash and, where the old file recorded one, its mode. The old file is not deleted, so you remove it yourself. A warning is printed when 2.0 reads the old file.
  baseline (cites lock-migration): When a 2.0 command finds an older `sablefile.lock` and no `.sablefile/lock.json`, it reads the old file and prints a war...
  unfiltered (cites lock-migration): When a 2.0 command finds an older `sablefile.lock` and no `.sablefile/lock.json`, it reads the old file and prints a war...
  second-model (cites lock-migration): The old `sablefile.lock` file from version 1.1 is not written to the new lock file, so it remains unchanged. [sec:lock-m...
q-0054 | version 2.0 | planted (stale-answer) | Does the 2.0 lock keep each generated file's mode, and what happens to modes from an old lock?
  reference: Yes. 2.0 records each generated file's mode in .sablefile/lock.json. When a 2.0 command migrates an older lock, it keeps each mode that the old file has.
  baseline (cites lock-mode lock-migration): Yes, the 2.0 lock keeps each generated file's mode, the Unix permission bits such as `0644`, in `.sablefile/lock.json` [...
  unfiltered (cites lock-mode lock-migration): Yes, the 2.0 lock keeps each generated file's mode, the Unix permission bits such as `0644`, in `.sablefile/lock.json` [...
  second-model (cites lock-mode lock-migration): The 2.0 lock keeps each generated file's mode, as specified in [sec:lock-mode]. When a lock file is migrated from `sable...
q-0055 | version 2.0 | planted (stale-answer) | How do I make sync retry a remote template fetch fewer times in 2.0?
  reference: Pass --retries N with the number you want, for example --retries 1. The flag sets the retry count for sync and diff; without it the default is five.
  baseline (cites retries-flag): Use the `--retries N` flag to set the number of times `sync` retries a failed fetch of a remote template, where N is a w...
  unfiltered (cites retries-flag): To make `sync` retry a remote template fetch fewer times in version 2.0, use the `--retries N` flag where N is a whole n...
  second-model (cites retries-flag): The `--retries` flag sets how many times `sync` and `diff` retry a failed fetch of a remote template, in place of the de...
q-0056 | version 1.0 | not planted | Does sablefile check need a network connection to run in 1.0?
  reference: No. check does not fetch remote templates or render templates, so it works without a network.
  baseline (cites check-command): No, sablefile check does not need a network connection to run. [sec:check-command]
  unfiltered (cites remote-fetch-failure): Yes, sablefile checks need a network connection to run in 1.0, as it requires fetching remote templates, and if a remote...
  second-model (declined): The docs don't say.
q-0057 | version 2.0 | not planted | Will check pick up a change that someone made on a remote template's server?
  reference: No. check never fetches remote templates, so only the next sync's output and the output of diff reflect that change.
  baseline (cites remote-retries): No, `check` does not see changes on a remote template's server. [sec:remote-retries]
  unfiltered (cites remote-retries): No, `check` does not fetch anything and never retries, so it will not pick up a change that someone made on a remote tem...
  second-model (cites remote-templates): Check does not see changes on a remote template's server. A change on the server affects what the next sync writes and w...
q-0058 | version 2.0 | not planted | If I run check --no-fail while drift is present, what does its printed output look like?
  reference: It still prints a DRIFT line and the path for each drifted file. The flag only changes the exit status to 0.
  baseline (cites quickstart-check): Run `sablefile check` after a sync. If no output appears, no generated file has drifted since the last sync. To see what...
  unfiltered (declined): The docs don't say.
  second-model (no citation): The check prints `DRIFT` and the path, and exits with status 1. A check with no drift exits with status 0. Pass `--no-fa...
q-0059 | version 1.1 | not planted | What is the mode that sablefile 1.1 stores for each generated file, and which command stores it?
  reference: The Unix permission bits of the file, such as 0644. sync saves it for every file it writes.
  baseline (cites lock-mode lock-mode): The mode that sablefile 1.1 stores for each generated file is the Unix permission bits, such as `0644` [sec:lock-mode]. ...
  unfiltered (cites lock-mode): The mode that sablefile 1.1 stores for each generated file is the Unix permission bits, such as `0644`. The `sync` comma...
  second-model (cites lock-mode lock-mode): The mode that sablefile 1.1 stores for each generated file is described in [sec:lock-mode]. The command that stores it i...
q-0060 | version 2.0 | not planted | What top-level keys does the 2.0 lock file JSON contain?
  reference: A format key, set to the string 2.0, and a files key that maps each generated path to its SHA-256 hash and mode.
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (no citation): The 2.0 lock file JSON contains keys: `lock.json`.
q-0061 | version 1.0 | not planted | What is the usual way to preview sync's changes in 1.0 before writing?
  reference: Run sablefile diff. It shows the differences between each rendered template and its target on disk, without writing any file or changing the lock.
  baseline (cites diff-command): Run `sablefile diff` to preview sync's changes before writing. [sec:diff-command]
  unfiltered (cites sync-default): To see the changes before they are written, run `sablefile diff`, which shows the same differences without writing anyth...
  second-model (cites diff-command): The usual way to preview sync's changes in 1.0 before writing is to use `sablefile diff`. [sec:diff-command]
q-0062 | version 2.0 | not planted | Can I point sablefile init at a folder other than the current one in 2.0?
  reference: Yes. Give the folder as an argument, such as init path/to/folder. The folder must already exist, and a relative path is read from the folder where you run the command.
  baseline (cites init-directory): Yes, you can point `sablefile init` at a folder other than the current one. To do this, provide the path to the folder a...
  unfiltered (cites init-directory): Yes, you can point `sablefile init` at a folder other than the current one in 2.0. To do this, give the folder as an arg...
  second-model (declined): The docs don't say.
q-0063 | version 1.1 | not planted | If a target sits in folders that do not exist yet, what does sync do in 1.1?
  reference: It creates the missing folders before it writes the file, so no setup is needed. sync never removes a folder, even one that ends up empty.
  baseline (declined): The docs don't say.
  unfiltered (cites sync-create-dirs): If a target sits in folders that do not exist yet, sync creates the folder before it writes the file in version 1.1. [se...
  second-model (no citation): The lockfile is `sablefile.lock` in the project root. It holds one line for each generated file: the SHA-256 hash of the...
q-0064 | version 2.0 | not planted | After I delete a target from sablefile.toml, does sync --apply in 2.0 remove its now-empty folder?
  reference: No. A sync run never deletes a directory, which means any empty ones you leave behind remain.
  baseline (cites sync-create-dirs): No, sync --apply does not remove empty folders. sync never removes a folder, so empty folders you leave behind stay wher...
  unfiltered (cites sync-create-dirs): No, sync --apply in 2.0 does not remove its now-empty folder. sync never removes a folder, so empty folders you leave be...
  second-model (declined): The docs don't say.
q-0065 | version 1.0 | not planted | Where can template files sit inside a 1.0 project?
  reference: Anywhere in the project. The template key in each [[file]] table gives the path from the project folder, and a template is read only when a command renders it.
  baseline (cites templates-location): Template files can sit in any folder of the project. [sec:templates-location]
  unfiltered (cites templates-location): Template files can sit in any folder of the project. [sec:templates-location]
  second-model (no citation): Template files are ordinary text files, and they can sit in any folder of the project. The `template` key in a `[[file]]...
q-0066 | version 2.0 | not planted | Does sablefile run any code that is inside a template?
  reference: No. Rendering only substitutes placeholders. It executes nothing in the template, and the same template with the same values always gives the same output.
  baseline (cites template-render): No, sablefile does not run any code that is inside a template. Rendering does not run code in the template. [sec:templat...
  unfiltered (cites template-render): No, sablefile does not run any code that is inside a template. Rendering does not run code in the template. [sec:templat...
  second-model (declined): The docs don't say.
q-0067 | version 1.1 | not planted | Can a [[file]] table in 1.1 take a template that lives at an https address?
  reference: Yes. The template key can name an https URL. sablefile fetches it when a command renders the template, and the fetched text is not copied into the project.
  baseline (cites remote-templates): Yes, a [[file]] table in 1.1 can take a template that lives at an https address. [sec:remote-templates]
  unfiltered (cites config-files-table): Yes, a [[file]] table in 1.1 can take a template that lives at an https address. [sec:config-files-table]
  second-model (declined): The docs don't say.
q-0068 | version 2.0 | not planted | What happens when a remote fetch in 2.0 still fails after every retry?
  reference: The command halts, reporting the failing address in its error message, and ends with status 1. Targets it never wrote retain their previous lock records.
  baseline (cites remote-fetch-failure): If a remote template still cannot be fetched after the last retry, the command stops with an error that names the URL, a...
  unfiltered (cites remote-fetch-failure): If a remote template still cannot be fetched after the last retry, the command stops with an error that names the URL, a...
  second-model (declined): The docs don't say.
q-0069 | version 1.0 | not planted | What exit status does sync give in 1.0 when a template file is missing?
  reference: Status 1. sync cannot finish in that case, and its error message names the file that caused the failure.
  baseline (cites sync-exit-status): Sync exits with status 1 when it cannot finish, for example when a template file is missing or a remote template cannot ...
  unfiltered (cites sync-exit-status): sync exits with status 1 when a template file is missing. [sec:sync-exit-status]
  second-model (cites sync-exit-status): The exit status for sync in 1.0 when a template file is missing is 1. [sec:sync-exit-status]
q-0070 | version 1.1 | not planted | If sync in 1.1 exits with status 0, does that mean the generated text is what I want?
  reference: Not necessarily. Status 0 only shows that sync finished, so you should open the generated files and check them.
  baseline (cites sync-exit-status): No, if sync exits with status 0, it only means that sync completed successfully, not that the generated text is what you...
  unfiltered (cites sync-exit-status): No, if sync in 1.1 exits with status 0, it does not mean the generated text is what you want. A status of 0 shows that s...
  second-model (declined): The docs don't say.
q-0071 | version 1.0 | not planted | Where do I list paths for sablefile 1.0 to leave alone, and what happens to them?
  reference: In the ignore file .sablefileignore in the project root, with one entry per line. Sync leaves an ignored target unwritten, check and diff both pass over it, and no lock record is made for it.
  baseline (cites ignore-file): You list paths for sablefile 1.0 to leave alone in the ignore file, `.sablefileignore`, which sits in the project root. ...
  unfiltered (cites ignore-file): List paths for sablefile 1.0 to leave alone in the `.sablefileignore` file, which sits in the project root. Put one entr...
  second-model (no citation): The ignore file, `.sablefileignore`, sits in the project root and lists paths that sablefile must leave alone. A project...
q-0072 | version 2.0 | not planted | With --apply, does 2.0's sync write a target that my ignore file lists?
  reference: No. An ignored target is never written, and it gets no lock record either.
  baseline (cites ignore-file): No, with `--apply`, 2.0's sync does not write a target that is listed in the ignore file. [sec:ignore-file]
  unfiltered (cites ignore-file): No, with --apply, 2.0's sync does not write a target that is listed in the ignore file. [sec:ignore-file]
  second-model (declined): The docs don't say.
q-0073 | version 2.0 | not planted | Which lines in a 2.0 ignore file are skipped as comments?
  reference: Lines that begin with a hash sign. Blank lines are also ignored.
  baseline (cites ignore-syntax): Lines that start with `#` are comments. [sec:ignore-syntax]
  unfiltered (cites ignore-syntax): Lines that start with `#` are comments. [sec:ignore-syntax]
  second-model (declined): The docs don't say.
q-0074 | version 1.1 | not planted | A check in 1.1 reports drift for a file I did not mean to change. What should I do first?
  reference: Start with diff, which shows how the file differs from its template. Keep wanted changes by moving them into the template before running sync; discard unwanted ones by reverting the file and running check again.
  baseline (cites troubleshoot-drift): Look at the change before you act. Run `sablefile diff` to see how the file differs from its template. [sec:troubleshoot...
  unfiltered (cites troubleshoot-drift): Look at the change before you act. [sec:troubleshoot-drift]
  second-model (cites check-command): Run `sablefile diff` to see how the file differs from its template. [sec:check-command]
q-0075 | version 2.0 | not planted | After installing the 2.0 archive, how do I confirm which version the shell is running?
  reference: Run sablefile --version. The output has the form sablefile 2.0, and that number should match the docs you are reading.
  baseline (cites install-check-version): Run `sablefile --version` to see the installed version. [sec:install-check-version]
  unfiltered (cites install-check-version): Run `sablefile --version` to see the installed version. The output has the form `sablefile 2.0`. Check that the number m...
  second-model (declined): The docs don't say.
q-0076 | version 1.0 | not planted | How do I remove sablefile 1.0 without losing my project's files?
  reference: Run python3 -m pip uninstall sablefile. That removes the command and its package, and leaves the project's own files alone, including the config, templates, outputs and lock.
  baseline (cites install-uninstall): To remove sablefile 1.0, run `python3 -m pip uninstall sablefile`. This removes the `sablefile` command and its package....
  unfiltered (cites install-uninstall): Run `python3 -m pip uninstall sablefile`. This removes the `sablefile` command and its package. It does not change your ...
  second-model (declined): The docs don't say.
q-0077 | version 2.0 | not planted | I installed sablefile but my shell says the command is not found. What should I check in 2.0?
  reference: Ask pip where it put the package, using pip show sablefile from that very same shell. If a location comes back yet the command fails, the scripts folder may be missing from your path.
  baseline (cites troubleshoot-command-not-found): If the shell reports that `sablefile` is not found, the command is not installed in the environment that is active. Run ...
  unfiltered (cites troubleshoot-command-not-found): If the shell reports that `sablefile` is not found, the command is not installed in the environment that is active. Run ...
  second-model (declined): The docs don't say.
q-0078 | version 1.1 | not planted | Does upgrading sablefile to a newer 1.x archive change any file in my project?
  reference: No. The upgrade writes no project file. Read the changelog in the newer version's folder first, since it lists each section whose behaviour changed.
  baseline (cites install-upgrade): No, installing a new version of sablefile does not write any project file. [sec:install-upgrade]
  unfiltered (cites install-upgrade): No, installing a new version does not write any project file. [sec:install-upgrade]
  second-model (declined): The docs don't say.
q-0079 | version 2.0 | not planted | After a 2.0 sync --apply, how do I confirm the template placeholder was filled in?
  reference: Open the target, such as README.md, and look for the project name in the spot where the placeholder stood.
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0080 | version 1.0 | not planted | What is the difference between a placeholder and a value in sablefile 1.0?
  reference: A placeholder is a name in a template that sync replaces. A value is the string in the [values] table that the placeholder's name points to.
  baseline (cites glossary-terms): A placeholder is a name in a template that sync replaces with a value, written as `{{project}}` in this version. A value...
  unfiltered (decline phrase with other text): The sections do not define or differentiate between a placeholder and a value in sablefile 1.0. [sec:template-render] de...
  second-model (no citation): The difference between a placeholder and a value in sablefile 1.0 is that a placeholder is a name in a template that syn...
## unanswerable: 13 dev items
q-0015 | version 1.0 | planted (false-premise) | In sablefile 1.0, what does the --dry-run flag on sync print?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0016 | version 2.0 | not planted | Does sablefile 2.0 run on Windows?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0017 | version 2.0 | not planted | How fast is sablefile check on a project with several thousand generated files?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0018 | version 1.1 | not planted | Can sablefile 1.1 fetch a remote template from a private URL that needs a login token?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (cites remote-retries): Yes, sablefile 1.1 can fetch a remote template from a private URL that needs a login token, as long as the token is incl...
  second-model (declined): The docs don't say.
q-0034 | version 1.1 | planted (false-premise) | In sablefile 1.1, what does sync --apply write to the lock file?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (cites sync-lock-update): The lock file is how check finds drift, so run sync after each change you intend to keep. Commit the lock file with the ...
q-0035 | version 1.0 | planted (false-premise) | Does check in sablefile 1.0 have a --no-fail option?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0036 | version 1.1 | planted (false-premise) | In sablefile 1.1, what does the --quiet flag on sync do?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (cites sync-default): The --quiet flag on sync is used to suppress the display of the diff output. It does not change the lock file or the syn...
q-0037 | version 1.0 | not planted | In sablefile 1.0, what happens when a template uses a placeholder whose name is not in [values]?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0038 | version 2.0 | not planted | Is there a maximum number of templates a 2.0 project can have?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0039 | version 1.1 | not planted | What exit status does sablefile diff return when it finds differences in 1.1?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (cites check-exit-status): When check finds a drifted file, it prints `DRIFT` and the path, and exits with status 1. [sec:check-exit-status]
  second-model (declined): The docs don't say.
q-0040 | version 2.0 | not planted | If a file listed in the lock is missing from disk, does check report it in 2.0?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0041 | version 2.0 | not planted | Is there a limit on how long a value in [values] can be?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0042 | version 1.0 | not planted | Can sablefile 1.0 set the output colour through a color key in sablefile.toml?
  reference: none: the item is unanswerable, so the right reply declines
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
## version-dependent: 17 dev items
q-0001 | version 1.1 | not planted | In sablefile 1.1, if I run sync with no flags, are the target files written straight away?
  reference: Yes. In 1.1 a plain sync writes each target and records it in the lock file. To preview the changes first, run diff, which shows them without writing anything.
  baseline (cites sync-default): Yes, if you run `sablefile sync` with no flags, the target files are written straight away. [sec:sync-default]
  unfiltered (cites sync-default): Yes, in sablefile 1.1, if you run `sync` with no flags, the target files are written straight away. This is because `sab...
  second-model (decline phrase with other text): The docs don't say. The docs don't say.
q-0002 | version 2.0 | not planted | In sablefile 2.0, if I run sync with no flags, are the target files written?
  reference: No. In 2.0 a plain sync prints a plan that lists what would be created or updated, and it writes nothing. Adding --apply makes sync write the targets and update the lock file.
  baseline (cites sync-default): No, the target files are not written when running `sablefile sync` with no flags. Instead, sync prints a plan and writes...
  unfiltered (cites apply-flag): No, in sablefile 2.0, if you run `sync` with no flags, the target files are not written. The `--apply` flag is required ...
  second-model (declined): The docs don't say.
q-0003 | version 1.0 | planted (version-swap) | In sablefile 1.0, is ${project} the right way to insert the project name into a template?
  reference: No. In 1.0 a placeholder is a name in double braces, written {{project}}. The text ${project} is not a placeholder in 1.0, so it is copied to the output unchanged.
  baseline (cites placeholders): No, `${project}` is not the right way to insert the project name into a template in sablefile. The correct way is to use...
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0004 | version 2.0 | not planted | In sablefile 2.0, is ${project} the right way to insert the project name into a template?
  reference: Yes. In 2.0 a placeholder is a name with a dollar sign and braces around it, so the form ${project} is replaced by the project value. The old double-brace form is an error.
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0021 | version 1.0 | not planted | In sablefile 1.0, does check give a nonzero exit status when a generated file has drifted?
  reference: No. In 1.0 check prints DRIFT and the path for a drifted file but exits with status 0, so a script has to read the printed lines to see drift.
  baseline (cites check-exit-status): No, check does not give a nonzero exit status when a generated file has drifted. The check command prints "DRIFT" and th...
  unfiltered (cites quickstart-check): Yes, in sablefile 1.0, `check` gives a nonzero exit status when a generated file has drifted. This is because, without t...
  second-model (cites check-exit-status): The check exits with status 0 even when files have drifted, so a script cannot detect drift from the exit status in this...
q-0022 | version 2.0 | not planted | In sablefile 2.0, does check give a nonzero exit status when a generated file has drifted?
  reference: Yes. check exits with status 1 when a file has drifted. Adding --no-fail changes that to status 0 while still printing the DRIFT lines.
  baseline (cites check-exit-status): Yes, check gives a nonzero exit status when a generated file has drifted. [sec:check-exit-status]
  unfiltered (cites no-fail-flag no-fail-flag): No, in sablefile 2.0, `check` does not give a nonzero exit status when a generated file has drifted if the `--no-fail` f...
  second-model (cites check-exit-status): The check exits with a nonzero exit status when a generated file has drifted. [sec:check-exit-status]
q-0023 | version 1.0 | not planted | Does an ignore entry of *.log in sablefile 1.0 skip a target at docs/build.log?
  reference: No. In 1.0 each entry is a shell glob matched against the whole target path, and shell globs do not match across folders. The entry only covers files at the top level of the project.
  baseline (cites ignore-syntax): Yes, an ignore entry of `*.log` in sablefile 1.0 skips a target at `docs/build.log`. [sec:ignore-syntax]
  unfiltered (cites ignore-syntax): Yes, an ignore entry of `*.log` in sablefile 1.0 skips a target at `docs/build.log`. [sec:ignore-syntax]
  second-model (cites ignore-syntax): The docs section does not skip the target at docs/build.log. The ignore entry of *.log in sablefile 1.0 does not skip th...
q-0024 | version 2.0 | not planted | Does an ignore entry of *.log in sablefile 2.0 skip a target at docs/build.log?
  reference: Yes. In 2.0 entries use gitignore syntax, so a line such as *.log matches at any depth, including docs/build.log.
  baseline (cites ignore-syntax): Yes, an ignore entry of `*.log` in sablefile 2.0 skips a target at `docs/build.log`. [sec:ignore-syntax]
  unfiltered (cites ignore-syntax): Yes, an ignore entry of `*.log` in sablefile 2.0 skips a target at `docs/build.log`. [sec:ignore-syntax]
  second-model (declined): The docs don't say.
q-0025 | version 1.0 | planted (version-swap) | Does the lock file in sablefile 1.0 record each generated file's mode?
  reference: No. In 1.0 each lock line holds only the SHA-256 hash and the path, so no mode is recorded.
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0026 | version 1.1 | not planted | Does the lock file in sablefile 1.1 record each generated file's mode?
  reference: Yes. Each lock line holds the SHA-256 hash, then the file's mode, then the path. check compares only the hash, so a change of mode alone is not reported as drift.
  baseline (cites lock-mode): Yes, the lock file in sablefile 1.1 records each generated file's mode. [sec:lock-mode]
  unfiltered (cites lock-mode): Yes, the lock file in sablefile 1.1 records each generated file's mode. [sec:lock-mode]
  second-model (cites lock-mode): The lock file in sablefile 1.1 records each generated file's mode. [sec:lock-mode]
q-0027 | version 1.0 | not planted | How many times does sablefile 1.0 retry a remote template fetch that keeps failing?
  reference: Three retries, after which the command gives up. No flag or setting changes that count in 1.0.
  baseline (cites remote-retries): Three times. [sec:remote-retries]
  unfiltered (cites remote-retries): Sablefile 1.0 retries a remote template fetch up to 3 times before giving up. [sec:remote-retries]
  second-model (cites remote-retries): The count is fixed in 1.0, and no flag or setting changes it. [sec:remote-retries]
q-0028 | version 1.1 | not planted | How many times does sablefile 1.1 retry a remote template fetch that keeps failing?
  reference: Five retries, after which the command gives up. In 1.1 no flag or setting can change that count.
  baseline (cites remote-retries): Sablefile 1.1 retries a remote template fetch up to 5 times before giving up. [sec:remote-retries]
  unfiltered (cites remote-retries): Sablefile 1.1 retries a remote template fetch up to 5 times before giving up. [sec:remote-retries]
  second-model (cites remote-retries): The count is fixed in 1.1, and no flag or setting changes it. [sec:remote-retries]
q-0029 | version 1.0 | planted (version-swap) | In sablefile 1.0, does sync --apply create the missing folder for a target?
  reference: The 1.0 docs describe no --apply flag. Sync creates a target's missing folder by itself, before it writes the file, so a target such as docs/guide/index.md needs no setup.
  baseline (cites sync-create-dirs): Yes, sync --apply creates the missing folder for a target. [sec:sync-create-dirs]
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0030 | version 2.0 | not planted | In sablefile 2.0, does sync --apply create the missing folder for a target?
  reference: Yes, but only because --apply is given. In 2.0 a plain sync creates no folder, since it writes nothing, and with --apply the folder is made before the target is written.
  baseline (cites sync-create-dirs): Yes, sync --apply creates the missing folder for a target. [sec:sync-create-dirs]
  unfiltered (cites apply-flag): Yes, sync --apply creates the missing folder for a target. [sec:apply-flag]
  second-model (cites sync-create-dirs): [sec:sync-create-dirs] Folders for targets   Yes, with `--apply`, sync creates the missing folders before writing the fi...
q-0031 | version 1.1 | planted (version-swap) | In sablefile 1.1, where is .sablefile/lock.json kept?
  reference: The 1.1 docs describe no .sablefile folder. The lock file in 1.1 is sablefile.lock in the project root, with one line for each generated file.
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0032 | version 2.0 | not planted | In sablefile 2.0, where is the lock file kept?
  reference: In .sablefile/lock.json, a JSON file with a format string and one entry per generated file. A leftover sablefile.lock from 1.x is read with a warning and migrated when a command writes files.
  baseline (cites lock-migration): In sablefile 2.0, the lock file is kept in `.sablefile/lock.json`. [sec:lock-migration]
  unfiltered (cites lock-migration): In sablefile 2.0, the lock file is kept in `.sablefile/lock.json`. [sec:lock-migration]
  second-model (cites lock-mode): The lock file is kept in `.sablefile/lock.json`. [sec:lock-mode]
q-0033 | version 2.0 | not planted | In sablefile 2.0, what does sync print for a target whose content already matches its template?
  reference: The word unchanged, as that target's plan line. The plan step itself writes nothing.
  baseline (declined): The docs don't say.
  unfiltered (cites apply-flag): For a target whose content already matches its template, sync prints "unchanged". [sec:apply-flag]
  second-model (declined): The docs don't say.
## ambiguous: 10 dev items
q-0019 | version 2.0 | planted (ambiguous-target) | If I edit the file and then run check, will it fail?
  reference: Reading 1: if you edited a generated file (a target), check prints DRIFT and the path for it and exits with status 1, because its hash no longer matches the lock.
Reading 2: if you edited a template, check prints nothing and exits with status 0, since a template change is not drift.
  baseline (cites quickstart-check check-exit-status): Yes, if you edit the file and then run `sablefile check`, it will report `DRIFT` and the path of the file, indicating a ...
  unfiltered (cites check-exit-status no-fail-flag): Yes, if you edit the file and then run `sablefile check`, it will detect the drift and print `DRIFT` and the path of the...
  second-model (cites check-exit-status): If you edit the file and then run `sablefile check`, it will fail because the check will detect a drift and print a `DRI...
q-0020 | version 2.0 | not planted | Does sync change the lock file?
  reference: Reading 1: a plain sync, with no flag, writes nothing, so the lock file is left alone.
Reading 2: sync --apply writes the targets and updates .sablefile/lock.json with the hash and mode of each file it wrote.
  baseline (cites sync-lock-update): Yes, sync changes the lock file when the `--apply` flag is used. After sync writes a target, it records that file's SHA-...
  unfiltered (cites diff-command): No, sync does not change the lock file. [sec:diff-command]
  second-model (cites sync-lock-update): The lock file is how check finds drift, so run sync after each change you intend to keep. [sec:sync-lock-update]
q-0043 | version 2.0 | planted (ambiguous-target) | Is it drifted now that I changed the template?
  reference: Reading 1: if 'it' means the target, it has not drifted. Nothing has edited the target since the last sync, so check prints nothing for it.
Reading 2: if 'it' means a target that you hand-edited after the last sync, it has drifted, and check prints DRIFT and exits with status 1.
  baseline (cites drift-meaning): No, it is not drifted now that you changed the template. A change to a template is not drift, because the generated file...
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0044 | version 2.0 | not planted | Does sync create a folder for a target?
  reference: Reading 1: a plain sync writes nothing, so it creates no folder.
Reading 2: sync --apply creates the target's missing folder before it writes the file.
  baseline (cites sync-create-dirs): Yes, sync creates a folder for a target if the folder does not exist, but only when the `--apply` flag is used. [sec:syn...
  unfiltered (declined): The docs don't say.
  second-model (cites sync-create-dirs): Yes, sync creates a folder for a target. [sec:sync-create-dirs]
q-0045 | version 2.0 | not planted | Does --retries change how often the command retries?
  reference: Reading 1: for sync and diff, yes. They use the count you give, in place of the default of five.
Reading 2: for check, no. check never fetches a remote template, so it never retries.
  baseline (cites retries-flag): Yes, the `--retries` flag changes how often the command retries a failed fetch of a remote template. [sec:retries-flag]
  unfiltered (cites retries-flag remote-retries): Yes, the `--retries` flag changes how often the command retries a failed fetch of a remote template. It sets the number ...
  second-model (cites retries-flag): The `--retries` flag changes how often the command retries a failed fetch of a remote template, in place of the default ...
q-0046 | version 2.0 | not planted | If I delete sablefile.lock, will check stop reporting drift?
  reference: Reading 1: if the old file was the only lock, deleting it leaves check with nothing to read, so check prints an error message instead of DRIFT lines.
Reading 2: once .sablefile/lock.json exists, 2.0 reads only that file, so deleting sablefile.lock changes nothing.
  baseline (declined): The docs don't say.
  unfiltered (declined): The docs don't say.
  second-model (declined): The docs don't say.
q-0047 | version 2.0 | not planted | When does a 2.0 project's old lock file get migrated?
  reference: Reading 1: a command that only reads, such as check, reads the old file and prints a warning, but writes nothing, so both files stay as they are.
Reading 2: a command that writes files, such as sync --apply, also writes .sablefile/lock.json and keeps each entry's mode where the old file has one.
  baseline (cites lock-migration): When a 2.0 command finds an older `sablefile.lock` and no `.sablefile/lock.json`, it reads the old file and prints a war...
  unfiltered (cites lock-migration): When a 2.0 command finds an older `sablefile.lock` and no `.sablefile/lock.json`, it reads the old file and prints a war...
  second-model (no citation): The 2.0 project's old lock file is migrated when a 2.0 command finds an older `sablefile.lock` and no `.sablefile/lock.j...
q-0048 | version 1.0 | not planted | In 1.0, does check report the file if I change it?
  reference: Reading 1: if 'the file' is a template, no. check does not render templates, so it prints nothing for a template change.
Reading 2: if 'the file' is a generated target you edited, yes. check prints DRIFT and the path for it.
  baseline (declined): The docs don't say.
  unfiltered (cites check-command): Yes, in 1.0, `check` reports the file if it is changed. [sec:check-command]
  second-model (cites check-command): The check command does not report the file if it changes. [sec:check-command]
q-0049 | version 2.0 | not planted | Will init overwrite my config?
  reference: Reading 1: if sablefile.toml already exists, init stops with an error and leaves it alone.
Reading 2: if you mean another file in the folder, such as a README, init writes no other file, so it does not touch that file.
  baseline (cites init-command): No, init will not overwrite your config. It stops with an error if `sablefile.toml` already exists, so it never overwrit...
  unfiltered (declined): The docs don't say.
  second-model (cites init-command): init stops with an error if `sablefile.toml` already exists, so it never overwrites your configuration. [sec:init-comman...
q-0050 | version 1.1 | not planted | Does the 1.1 lock file care about a file's mode?
  reference: Reading 1: yes, the lock records each generated file's mode alongside its hash.
Reading 2: no, for comparison. check compares only the hash, so a mode-only change is not reported as drift.
  baseline (cites lock-mode): Yes, the 1.1 lock file cares about a file's mode. [sec:lock-mode]
  unfiltered (cites lock-mode): Yes, the 1.1 lock file cares about a file's mode. The mode field is described in lock-mode, and sync records the mode of...
  second-model (cites lock-mode): The 1.1 lock file does not care about a file's mode. The mode field is described in lock-mode. [sec:lock-mode]
```

Take item q-0005. It asks whether sablefile 2.0 still reads sablefile.lock in the project root, and it is a planted near-miss term, a name close to one the docs use, which catches a careless reply. The baseline says no and cites a section about upgrading. The reference answer says that 2.0 falls back to the file, with a warning, so the baseline's no is wrong. The unfiltered and second-model variants both decline, and the docs do answer the question, so their declines are wrong as well.

The three replies to q-0005 fail in two different ways. A decline on an answerable item and a confident wrong answer are different failures, and a check that catches one doesn't catch the other. A pass rate would count all three replies as failures and lose that difference. The note on this reply in the data file begins "says 2.0 never reads sablefile.lock; reference says it falls back to it with a warning." Each note says what the reply did and what the reference says, in one sentence, so the grouping that follows rests on something a reader can check. A count can come from different defects, and two replies that both fail a pass rate can be different failures. That is why the replies come before the count.

The comparison has limits, and they bound what the counts can claim. The dev items were written to probe the assistant, and the planted items are not a random sample of what users ask. So the counts say which variant fails in which way on these items. They don't say how often a user would meet each failure. A sample of questions drawn the way users ask them would be needed for that.

**Working rule:** Before you count anything, read replies from every variant, grouped by kind, and write down what is wrong with each one. A count can say that a variant fails. Only the replies say how.

## Coding the failures {#coding-the-failures}

Reading becomes counting once each reply has a note and a mode. The drafting model wrote one note per reply, as the one on q-0005 does, and then grouped the notes. Each reply got one mode, its main defect, and a reply with no defect got `ok`. The codes were made by the AI model that drafted this book, as one coder; no second coder checked them, and nobody measured agreement on the codes. The 80 dev items give 240 replies, 80 from each variant. The codes sit in a data file beside the examples, one entry per reply.

The counts carry the label "coded by the drafting model (one coder; not human labels)", and the label means what it says. This chapter has no agreement figure, and no one else has reproduced the counts. [Chapter 1](measure-before-you-change) made the same point: agreement with your own labels doesn't calibrate a judge. [Chapter 6](calibrate-the-judge) takes that up.

The tally example turns the notes into counts, and it checks the codes first. Each dev item has exactly one code per variant, no code names a mode the file doesn't define, and the file carries the label. Then it prints one row per mode and one column per variant, and one labelled line for each count, which are the numbers the prose below quotes.

Example `tally-failure-modes` (Python 3.12.15 · numpy 2.5.5 · pydantic 2.14.3 · typing-extensions 4.16.0), passing in Edition 2026.11.3:

```python
"""Counts the drafting model's failure codes over the dev items, per variant, and prints one table and one labelled line
per count.

The point rests on the table's reading of each mode: the codes were made by the drafting model, as one coder, and are not
human labels. The codes live in data/failure-codes.json; the checks below stop a reply being counted twice or left out.
The labelled lines are the numbers the chapter's prose quotes."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import json
from collections import Counter
from pathlib import Path

from lib.testset import load_items

CODES = Path(__file__).resolve().parent / "data" / "failure-codes.json"
VARIANTS = ("baseline", "unfiltered", "second-model")

book = json.loads(CODES.read_text(encoding="utf-8"))
assert book["labelled"] == "coded by the drafting model (one coder; not human labels)", "the codes are the model's, not human labels"  # the label the prose uses
assert book["variants"] == list(VARIANTS), "the variants in the file are the three the chapter names"

dev_ids = {item.id for item in load_items(split="dev")}
n = len(dev_ids)
codes = book["codes"]
assert {code["item"] for code in codes} <= dev_ids, "a code names an item that is not in the dev split"
pairs = [(code["item"], code["variant"]) for code in codes]
# One code per dev item and variant: a pair repeated would be counted twice, a missing one would go unseen.
assert len(pairs) == len(set(pairs)) == n * len(VARIANTS), "expected one code per dev item and variant"
assert all(code["mode"] in book["modes"] for code in codes), "a code uses a mode the file does not define"

counts = Counter((code["variant"], code["mode"]) for code in codes)
print(f"dev items: {n}")
print(f"replies coded: {len(codes)}")
print(f"labelled: {book['labelled']}")
print(f"{'mode':<22}" + "".join(f"{variant:>14}" for variant in VARIANTS))
for mode in book["modes"]:  # the file's order: ok first, then the failure modes
    total = sum(counts[(variant, mode)] for variant in VARIANTS)
    if total == 0:  # a mode no variant shows is printed as zero of N, so the reader sees it was looked for
        print(f"{mode}: 0 of {n}")
        continue
    print(f"{mode:<22}" + "".join(f"{counts[(variant, mode)]:>14}" for variant in VARIANTS))
totals = {variant: sum(counts[(variant, mode)] for mode in book["modes"]) for variant in VARIANTS}
assert all(total == n for total in totals.values()), "each variant's counts add up to the dev items"
print(f"{'all modes':<22}" + "".join(f"{totals[variant]:>14}" for variant in VARIANTS))
print()
for variant in VARIANTS:  # one labelled line per count, the form the chapter's prose binds to
    for mode in book["modes"]:
        print(f"{mode}, {variant}: {counts[(variant, mode)]}")
    print(f"defective, {variant}: {n - counts[(variant, 'ok')]}")
```

Output:

```text
dev items: 80
replies coded: 240
labelled: coded by the drafting model (one coder; not human labels)
mode                        baseline    unfiltered  second-model
ok                                56            49            24
over-declining                    10            15            31
wrong-version-answer               2             3             0
wrong-answer                       3             5             9
missed-refusal                     0             2             2
incomplete-answer                  8             4             7
citation-problem                   1             2             6
malformed-reply                    0             0             1
all modes                         80            80            80

ok, baseline: 56
over-declining, baseline: 10
wrong-version-answer, baseline: 2
wrong-answer, baseline: 3
missed-refusal, baseline: 0
incomplete-answer, baseline: 8
citation-problem, baseline: 1
malformed-reply, baseline: 0
defective, baseline: 24
ok, unfiltered: 49
over-declining, unfiltered: 15
wrong-version-answer, unfiltered: 3
wrong-answer, unfiltered: 5
missed-refusal, unfiltered: 2
incomplete-answer, unfiltered: 4
citation-problem, unfiltered: 2
malformed-reply, unfiltered: 0
defective, unfiltered: 31
ok, second-model: 24
over-declining, second-model: 31
wrong-version-answer, second-model: 0
wrong-answer, second-model: 9
missed-refusal, second-model: 2
incomplete-answer, second-model: 7
citation-problem, second-model: 6
malformed-reply, second-model: 1
defective, second-model: 56
```

Read the `ok` row, then the rows under it. The baseline has the most replies with no defect, 56, and the second-model variant has the fewest, 24. Over-declining is the largest defect in each variant. In the second-model variant it is more than half of the defects: 31 of 56.

The baseline doesn't escape the worse defects. It gives 2 wrong-version answers, on q-0023 and q-0029, and the unfiltered variant gives the most, 3. Missed refusals come only from the variants, and the baseline has none. Every mode appears at least once. A mode that no variant showed would print as zero, so a reader could see it was looked for.

**Working rule:** Give each reply one note and one mode, and print one labelled line per count, so that every number the prose gives can be checked against the output.

## Over-declining {#over-declining}

An over-declining reply declines an item the docs answer. It is the defect a reader meets first, because a decline looks careful, and it fails the user as surely as a wrong answer does. The terms used here, the decline phrase, the unanswerable item and the variants, are defined in [what the replies look like](#what-the-replies-look-like). The count covers every item the docs answer, version-dependent items included, so for the baseline it is larger than the false refusal rate in [chapter 10](declining-when-the-docs-dont-say), which counts answerable items only. Item q-0004 is the version-dependent case that [chapter 1](measure-before-you-change#declines-in-code) explains in full. All three variants decline it with the same words, so the baseline does this too.

Counting declines has a trap, and it sits in the parser. Item q-0080 is answerable, and the unfiltered variant's reply to it gives two sentences saying the sections don't define the difference, then ends with the decline phrase. The docs answer the question, so the reply is an over-decline. The parser counts a decline only when the phrase is the whole reply, so it reads this one as an answer that cites a section. A reader who searches for the phrase finds it, and a check built on the parser misses it.

The check candidate is that a reply to an item whose reference names a supporting section must not decline, in any words. [Checks in code](checks-in-code) builds checks of that kind. Whether a decline is right on an item the docs don't cover is a judgement, which [chapter 10](declining-when-the-docs-dont-say) takes up.

**Working rule:** Count a decline by what the reply does, not by whether the phrase stands alone, and count over-declining apart from wrong answers, because their checks differ.

## Wrong-version answers {#wrong-version-answers}

A wrong-version answer gives another version's behaviour for the version the question asks about, and it can be fluent and cited while being wrong. In q-0029 the baseline says yes, `sync --apply` creates a missing folder in 1.0, and cites the section on creating folders. The note on the reply says that is the 2.0 behaviour, and that 1.0 has no `--apply` flag at all.

The unfiltered variant does this more often. In q-0021 it says yes to whether `check` gives a nonzero exit status for drift in 1.0, where the baseline and the second-model variant both answer that it does not. The note says the unfiltered reply gave the 2.0 rule for a 1.0 question. Its context holds every version, so the 2.0 rule sits beside the 1.0 one.

Citations don't settle it. In q-0023 the baseline answers yes about a 2.0 result, and it cites the 1.0 section. A check that every citation names a section of the asked version passes that reply. Only the claim, read against the 1.0 reference, shows the error.

**Working rule:** Check each reply's version in two places. Its citations must belong to the asked version, and its claim must match that version's reference. A citation check alone passes an answer that is right about the wrong version.

## Missed refusals {#missed-refusals}

A missed refusal answers an unanswerable item with content the docs don't hold. It is the mode a reader is most likely to believe, because the reply reads like any other answer. The terms used here are defined in [what the replies look like](#what-the-replies-look-like). The dev items show it only in the variants, 2 times in the unfiltered variant and 2 in the second-model variant, and each is short enough to read whole.

In q-0018 the unfiltered variant says a login token can be sent with a remote template fetch, and cites a section about retries. In q-0034 the second-model variant gives a tip about the lock file, cited to a section that doesn't cover the question. In q-0036 it says `--quiet` suppresses the diff output, citing a section that never mentions the flag. In q-0039 the unfiltered variant answers about `check` when the question asks about `diff`. The baseline declines every one of them.

A code check can require a decline on every unanswerable item, and it would catch each of them. On an answerable item the same fault goes unseen: a reply that cites a real section silent on its claim would pass, because it answers, as an answer is expected there. Reading the claim against the cited section is the work of [chapter 9](grounded-answers) and of [chapter 10](declining-when-the-docs-dont-say).

**Working rule:** Require a decline on every unanswerable item, and read every answer to one against the section it cites before you count it as right.

## From a failure to a check {#from-a-failure-to-a-check}

A failure mode is useful once it has a check candidate, and a candidate has four parts: the mode, the input the check reads, the claim it tests, and what it can't see. A candidate with no stated limit hasn't been thought through. A candidate is also not yet a check. [Checks in code](checks-in-code) builds the checks a program can run, and the judgements go to a judge. The list gives each of the seven failure modes from [coding the failures](#coding-the-failures) its candidate, and names the case that shows it.

- **Over-declining.** A reply to an item whose reference names a supporting section must not decline, in any words. The check can't tell a right decline on an item the docs don't cover from a wrong one, so that judgement goes to [chapter 10](declining-when-the-docs-dont-say).
- **Wrong-version answers.** Every citation must belong to the asked version, and the claim must match that version's reference. The first half is a code check in [checks in code](checks-in-code). The second, which catches q-0023, is version-correctness in [chapter 9](grounded-answers). It can't see a claim the reference doesn't cover.
- **Wrong answers.** The claim must match the reference answer for the asked version, and a reply to an ambiguous item must answer each reading, as [one judge](measure-before-you-change#one-judge) sets out. A judge with a written rubric compares each claim with its reference, as in [chapter 5](a-judge-with-a-rubric). Its test case is q-0005, where the baseline says 2.0 never reads sablefile.lock and the reference says it falls back to it. For ambiguous items the rubric must put both readings in the reference, as q-0048 needs: the unfiltered variant says yes and the second-model variant says no, and each is wrong about one reading. The judge can be wrong too, which [chapter 6](calibrate-the-judge) measures.
- **Missed refusals.** Every reply to an unanswerable item declines, or a reader checks its citation against the section it names. The first is a code check. The second is the work of [chapter 9](grounded-answers). The code check reads no section text, so on an answerable item it passes a reply that cites a real section silent on its claim.
- **Incomplete answers.** The reference lists each number, step and reading a right answer needs, and a code check could look for each one in the reply. This book builds no such check. In q-0011 the baseline says the retry count is fixed and that no flag changes it, but never gives the number. The unfiltered variant does give it, so a check for the reference's number would fail the baseline's reply. Its limit: a number can appear in the reply without being the answer.
- **Citation problems.** Every citation must be one of the item's supporting sections. In q-0057 the baseline is right that `check` doesn't see changes on a remote server, but it cites a section the item doesn't list as supporting, so the citation is unlisted. A code check against that list catches it. Its limit: a listed section can still fail to support the claim, which takes a reader, as [checks in code](checks-in-code) explains.
- **Malformed replies.** A check on the reply's shape, against the format the prompt asks for, catches a reply that comes out in the wrong order. The second-model reply to q-0030 puts its citation first and garbles its sentence, though its answer is right. Its limit: shape says nothing about the answer, so a reply can pass the shape check and still be wrong. The format checks in [checks in code](checks-in-code) build it.

Each candidate in the list names the reply it would have caught, and that is its first test. If a candidate doesn't flag the reply it was written for, it isn't yet a check for the mode.

Build the code checks first. They run in seconds and need no model call, so they can run on every change. A judge costs a model call for each reply and needs its own calibration, so it goes to the modes that a reference and a citation can't settle. Wrong answers need one for the claim. Wrong-version answers need one only for the part that reads a claim against its reference, and missed refusals need one only for the part that reads a claim against the section it cites.

In production the modes don't arrive labelled. A user reports a wrong reply, and the first question is which mode it is, because a check written for the wrong mode passes the reply that failed. When no mode fits, read the failing replies again, code them, add a mode and write its check. This is why the chapter reads and codes the replies before it counts anything.

The list isn't closed: the held-out items and any later variant will show modes these items don't, and each will need its own note and its own candidate.

The chapter made these decisions:

- One coder made the codes: the drafting model. They are labelled as such, and no agreement is measured.
- The dev items are the only items read here; the held-out decline counts appear in chapter 10.
- The baseline's replies are counted with the variants, so its 2 wrong-version answers are reported as such.

**Working rule:** Code the replies by their main defect before you choose a check, and write each check for one mode. A check built from the failures you expected tests for those failures, and it passes the ones you didn't expect.
