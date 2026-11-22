---
title: "Securing LLM Applications and Agents"
chapter: "Check what third parties hand the assistant"
chapter_id: third-party-parts
book: securing-llm-applications-and-agents
edition: 2026.11.2
verified: 2026-11-22
edition_code: Y3X2-HXT9
canonical: https://rollingedition.com/securing-llm-applications-and-agents/third-party-parts
license: CC BY-NC 4.0
more_permissions: https://rollingedition.com/policies/reuse
attribution: "“Check what third parties hand the assistant,” chapter 10 of Securing LLM Applications and Agents, Edition 2026.11.2, examples passed Nov 22, 2026. By Rolling Edition, https://rollingedition.com/securing-llm-applications-and-agents/third-party-parts. Text CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/), with added permissions (https://rollingedition.com/policies/reuse). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Check what third parties hand the assistant

By the end of this chapter you can check the parts of an assistant that other people wrote: the tools a server offers, the files of the model the assistant loads, and the packages its code installs. You'll test a tool's declared effects and arguments against what the tool does, pin a tool definition so that a later change is caught, check model files by hash and scan them before anything reads them, and see what a version pin fixes and what it leaves open.

Chapters 6 to 9 trusted the tools, model files and packages themselves. The office's assistant does not work from its own code alone. Two of its eight tools, `list_slots` and `book_visit`, come from a contractor's server. The host reads each tool's name, description, parameters and annotations and passes them to the model along with the prompt, and the model decides what to call from those words. Nobody at the office reads them first. On dev, the injections placed in tool descriptions reached the model through the tool block of its prompt, and [chapter 3](#undefended-baseline) counts them. Three kinds of claim need checking: what a tool declares it does, whether its definition is still the one that was approved, and whether the files and packages that run on the office's machines are the ones someone reviewed.

The definitions come from [Model Context Protocol in Practice, chapter 9](https://rollingedition.com/model-context-protocol-in-practice/s/tool-poisoning), which uses the terms this chapter keeps. In that chapter, a *tool definition* is "text from its server that the host passes to the model: its description, input schema and annotations."

Tool poisoning, in the same terms, "puts instructions for the model into a tool's definition." None of the checks in this chapter reads a description for instructions. The behaviour check tests declared effects and argument names against what the tool does, and the pin tests whether a definition is still the one a person approved. A poisoned description is caught when a person reads it at approval, which the same chapter covers under [tool poisoning](https://rollingedition.com/model-context-protocol-in-practice/s/tool-poisoning).

A *rug pull* is the change that follows approval: "a server changes a definition after the user approved it." The agreement the user gave no longer covers what the model is reading. The pin is the check for that change, and it is the subject of the second section.

The risk sits in the threat model. [Chapter 2](#risks-mapped) files a third party's definitions or outputs entering the prompt under ASI04 Agentic Supply Chain Vulnerabilities, from the OWASP Top 10 for Agentic Applications (Dec 9, 2025). MITRE ATLAS lists tool poisoning as AML.T0110, as [MITRE's D3FEND page for that technique](https://d3fend.mitre.org/offensive-technique/attack/AML.T0110/) states, and a rug pull as AML.T0109, as [the D3FEND page for that technique](https://d3fend.mitre.org/offensive-technique/attack/AML.T0109/) states.

## Declared effects are claims {#descriptions-are-claims}

A tool declares its effect in its annotations: `readOnlyHint` says that it only reads, and `destructiveHint` says that it may write. Its parameters name the arguments it takes. Those are claims the server makes, and a server can put a read-only label on a tool that writes. The host does not test the claim, so the check below does.

In production the drift is rarely deliberate. A vendor adds a tool that writes and forgets the label, a tool gains an argument its schema never names, or a write begins to touch a second table. Nobody notices until a reviewer happens to read the declaration and the code together. A check that runs whenever the definition changes turns that reading into a routine step.

The check tests the claims in three steps. It compares each tool's declared arguments with the arguments its code reads, which it collects from subscripts, `get` calls and `in` tests in the code's syntax tree. It takes the declared effect from the annotations. Then it makes one fresh call on a copy of the office's state and records which state fields changed. A read claim must come with no write, and a write claim must come with a write to exactly the tables approved when the tool was reviewed. A tool that declares no effect is not taken as a read: it disagrees if it writes, and it is `undeclared` if it does not.

Example `description-behaviour-check` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""Each contractor tool's declared arguments and effect are checked against what its tool does on a fresh call: the tables it writes, and the arguments its code reads, recorded by a proxy.

The check catches a mislabelled effect (a read-only or undeclared tool that writes, or a write whose tables are not the approved ones) and a mislabelled argument list (an argument the code reads that the schema does not name, or one the schema names that the code never reads). It does not judge the text of a description: an instruction written into a description is tool poisoning, and this check does not detect it.

The point rests on the book_visit lines. The contractor's listing declares no annotations, so the check reports that book_visit writes without a declared write: an open gap, pinned here. The copy that declares a write to the approved tables agrees; the copy that claims read-only while it writes must disagree.
"""
from lib import cases, pinning, threat, tools  # lib first: threads and seeds are fixed before anything else loads

APPROVED_WRITES = {"book_visit": ("bookings", "slots")}  # the tables book_visit was approved to write, from its review
EXPECTED = {"book_visit": "disagrees", "list_slots": "undeclared"}  # the contractor's listing declares no annotations


def observed(name: str, world: cases.World, acting: str) -> tuple[list[str], list[str]]:
    """The state fields a call changes on a fresh episode, and the argument keys the tool's code reads from its args."""
    state = tools.ToolState.new(acting)  # fresh, so one call's writes are not seen by the next
    recorder = pinning.ReadRecorder(threat.sample_args(world, state)[name])
    before = threat.snapshot(state)
    tools.call_tool(name, recorder, state)
    after = threat.snapshot(state)
    return sorted(f for f in threat.STATE_FIELDS if after[f] != before[f]), sorted(recorder.read)


def check(tool: dict, world: cases.World, acting: str, approved, case: str) -> str:
    """Prints the declared and observed facts for one definition, labelled by its case, and returns its verdict."""
    name = tool["name"]
    declared = pinning.declared_effect(tool)
    writes, reads = observed(name, world, acting)
    declared_args = set(tool["parameters"])
    print(f"declared arguments, {name}, {case}: {', '.join(sorted(declared_args))}")
    print(f"observed arguments, {name}, {case}: {', '.join(reads)}")
    print(f"declared effect, {name}, {case}: {declared}")
    print(f"observed writes, {name}, {case}: {', '.join(writes) or 'none'}")
    verdict = pinning.claim_verdict(declared, writes, approved) if declared_args == set(reads) else "disagrees"
    print(f"verdict, {name}, {case}: {verdict}")
    return verdict


def main():
    world = cases.load_world()
    acting = cases.load_tasks()[0].acting_user  # any staff member; the sample calls do not depend on the role
    server = pinning.load_json_strict((cases.DATA / "contractor.json").read_text(encoding="utf-8"))["tools"]

    for tool in sorted(server, key=lambda t: t["name"]):
        verdict = check(tool, world, acting, APPROVED_WRITES.get(tool["name"], ()), "contractor")
        assert verdict == EXPECTED[tool["name"]], f"{tool['name']}: {verdict}"

    # A copy that declares a write to the approved tables: the claim agrees with what the call does.
    book = next(t for t in server if t["name"] == "book_visit")
    declared_write = dict(book, annotations={"readOnlyHint": False})
    assert check(declared_write, world, acting, APPROVED_WRITES["book_visit"], "declared write") == "agrees"

    # The same copy with a second table written that was not approved: it disagrees.
    assert check(declared_write, world, acting, ("bookings",), "second table") == "disagrees"

    # The copy that claims read-only while the same call still writes: it disagrees.
    lying = dict(book, annotations={"readOnlyHint": True})
    assert check(lying, world, acting, APPROVED_WRITES["book_visit"], "read-only copy") == "disagrees"


if __name__ == "__main__":
    main()
```

Output:

```text
declared arguments, book_visit, contractor: contractor_id, slot_id, ticket_id
observed arguments, book_visit, contractor: contractor_id, slot_id, ticket_id
declared effect, book_visit, contractor: undeclared
observed writes, book_visit, contractor: bookings, slots
verdict, book_visit, contractor: disagrees
declared arguments, list_slots, contractor: contractor_id, date_from, date_to
observed arguments, list_slots, contractor: contractor_id, date_from, date_to
declared effect, list_slots, contractor: undeclared
observed writes, list_slots, contractor: none
verdict, list_slots, contractor: undeclared
declared arguments, book_visit, declared write: contractor_id, slot_id, ticket_id
observed arguments, book_visit, declared write: contractor_id, slot_id, ticket_id
declared effect, book_visit, declared write: write
observed writes, book_visit, declared write: bookings, slots
verdict, book_visit, declared write: agrees
declared arguments, book_visit, second table: contractor_id, slot_id, ticket_id
observed arguments, book_visit, second table: contractor_id, slot_id, ticket_id
declared effect, book_visit, second table: write
observed writes, book_visit, second table: bookings, slots
verdict, book_visit, second table: disagrees
declared arguments, book_visit, read-only copy: contractor_id, slot_id, ticket_id
observed arguments, book_visit, read-only copy: contractor_id, slot_id, ticket_id
declared effect, book_visit, read-only copy: read-only
observed writes, book_visit, read-only copy: bookings, slots
verdict, book_visit, read-only copy: disagrees
```

The contractor's listing declares no annotations at all. The check reports `book_visit` as `disagrees`, because the call writes `bookings, slots` and no write is declared. That is a gap in the contractor's listing, and the book pins it as it stands. The verdict for `list_slots` is `undeclared`: it declares nothing and its call writes no state field, so the claim is neither held nor broken.

The check holds when the declaration is right. The script builds a copy of `book_visit` that declares a write, and its verdict is `agrees`. The same copy with only `bookings` approved disagrees, `disagrees`, because the call also writes `slots`. The third copy declares read-only, and its call still writes `bookings, slots`, so the verdict is `disagrees`.

A pin would not catch that third copy. A pin proves that a definition has not changed since it was approved. It says nothing about whether the approved claim was true, so this check has to run as well.

The check has limits, and the output shows some of them. It makes one call per tool with the arguments the script supplies, on the office's fixture state, and it compares only the state fields the snapshot covers. A write that happens only with other arguments, or in a field outside the snapshot, is not seen. An argument read by iterating over the whole argument dict is not seen either, so a branch that reads its arguments that way escapes the argument comparison. A verdict of `agrees` means the claim held on this call. It is not a proof about every call.

**Working rule:** Before a third-party tool is offered to the assistant, check its declared effect and arguments against its behaviour. A read claim should come with no write, a write claim with a write to the approved tables, and every declared argument should match an argument the code reads. Run the check on the definition the server offers, and run it again whenever that definition changes.

## Pinning tool definitions {#pinning-tool-definitions}

The primary defence is the host's approval of each definition before the tool is offered, with the pin as its record. [Model Context Protocol in Practice, chapter 9](https://rollingedition.com/model-context-protocol-in-practice/s/pin-tool-definitions) teaches the pin and its attack, so this section does not repeat that. It adds what this book measures and the behaviour check the pin does not cover.

The pin here is a SHA-256 hash over every key of a tool's definition: its name, description, parameters, annotations and any other key the server sends, serialised as canonical JSON with each string in NFC form. Key order does not matter, and any value does. A later change to `readOnlyHint`, a single doubled space, or an added `title` changes the pin.

Next comes the rug pull, built in code. The script makes a copy of the contractor's server in which the carrier tool's description gains the sentence of one dev attack. The output prints the case ID and never the sentence. The carrier is `a-049`, the changed tool is `book_visit`, and its verdict is `changed`.

Example `pin-tool-definitions` (Python 3.13.16 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""The contractor's two tools verify against their pins; a changed copy, a duplicate listing and an added key do not, and the listing gate offers only verified tools, frozen.

The point rests on the verdict for book_visit in the changed copy: it is "changed", so the tool is not in the list the model gets. The pins are the hashes approved when the tools were first trusted. Added keys, duplicate names and frozen copies are in third-party-bypasses.
"""
from lib import cases, pinning  # lib first: threads and seeds are fixed before anything else loads

from pathlib import Path

PINS = Path(__file__).resolve().parent / "data" / "third-party" / "pins.json"


def main():
    server = pinning.load_json_strict((cases.DATA / "contractor.json").read_text(encoding="utf-8"))["tools"]
    pins = pinning.read_pins(PINS, "contractor")
    print(f"tools offered by the server: {len(server)}")
    print(f"tools pinned: {len(pins)}")

    # Unchanged definitions verify against their pins.
    verdicts = pinning.check_pins(pins, server)
    for name in sorted(verdicts):
        print(f"verdict, unchanged definition, {name}: {verdicts[name]}")
    assert all(v == "verified" for v in verdicts.values()), "an unchanged contractor tool must verify"

    # The hash reads the fields, not the order the server wrote them in: reversed keys give the same hash.
    tool = server[0]
    reordered = dict(reversed(list(tool.items())))
    same = pinning.definition_hash(reordered) == pinning.definition_hash(tool)
    print(f"same hash with keys reordered, {tool['name']}: {same}")
    assert same

    # A rug pull, built here as a modified copy: the carrier tool's description gains the attack's sentence.
    attacks = pinning.load_json_strict((cases.DATA / "attacks.json").read_text(encoding="utf-8"))["cases"]
    case = sorted((c for c in attacks if c["location"] == "loc-tool-description" and c["split"] == "dev"),
                  key=lambda c: c["id"])[0]  # the first dev attack carried in a description; its text is never printed
    carrier_tool = case["carrier"]["tool"]
    rugged = pinning.rugged_copy(server, carrier_tool, case["injection"])
    print(f"carrier case: {case['id']}")
    print(f"changed tool: {carrier_tool}")

    changed = pinning.check_pins(pins, rugged)
    for name in sorted(changed):
        print(f"verdict, after the change, {name}: {changed[name]}")
    assert changed[carrier_tool] == "changed"

    # The listing gate: the model is offered only the tools whose verdict is verified.
    listed = [tool["name"] for tool in pinning.listable(pins, rugged)]
    print(f"tools listed to the model after the change: {', '.join(listed)}")
    assert carrier_tool not in listed and len(listed) == len(server) - 1


if __name__ == "__main__":
    main()
```

Output:

```text
tools offered by the server: 2
tools pinned: 2
verdict, unchanged definition, book_visit: verified
verdict, unchanged definition, list_slots: verified
same hash with keys reordered, list_slots: True
carrier case: a-049
changed tool: book_visit
verdict, after the change, book_visit: changed
verdict, after the change, list_slots: verified
tools listed to the model after the change: list_slots
```

The listing step is the host's gate on which tools reach the prompt. In the example the gate is `pinning.listable`, and it offers only the tools whose verdict is verified. The only tool listed to the model after the change is `list_slots`. Of the two contractor tools, `2` have pins, and both verify before the change. The gate lists frozen copies, made after the check from the canonical form that was hashed, so the listed object cannot change after the check. A host that lists through `pinning.listable` would not send the changed tool to its prompt. The office's harness does not use the gate: it builds its tool block from the contractor's file, so this is a demonstration of the gate, not of the office's route.

A server with no pins gives the gate nothing to compare. A tool with no pin is `unpinned`, and it is not listed. The risk is a host that writes pins automatically on the first load, so the first load's definitions pass without a reading by anyone. The host should refuse to start a server whose pins are missing, and a person should take the pins.

Example `third-party-bypasses` (Python 3.13.16 · bm25s 0.3.16 · linkify-it-py 2.2.0 · markdown-it-py 4.3.0 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""The chapter 10 review's regression rows for the third-party parts, as data: pins, requirement lines, claims, stand-in argument reads and model folders.

Each row runs through lib/regressions.py, which asserts its expected verdict and prints the verdicts by name. Each row's expected verdict is the one the current code gives; a row that a later change alters fails the assertion.
"""
import tempfile
from pathlib import Path

from lib import cases, pinning, regressions  # lib first: threads and seeds are fixed before anything else loads


def _pins_refused(path: Path, server: str) -> bool:
    """True when read_pins refuses the file for this server, as the review's fix does for another server's file."""
    try:
        pinning.read_pins(path, server)
    except ValueError:
        return True
    return False


def _duplicate_description_refused(text: str) -> bool:
    """True when the strict reader refuses a definition with a repeated key, rather than keeping one of the two."""
    try:
        pinning.load_json_strict(text)
    except ValueError:
        return True
    return False


def main():
    world = cases.load_world()
    verdicts = regressions.check("third-party", world)  # asserts each attempt's expected verdict
    print(f"attempts asserted: {len(verdicts)}")
    regressions.report(verdicts)

    # S10-15: the pins file says it is for another server. The reader must refuse it for this server. The control is a
    # file written for this server, which the same reader must load.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pins.json"
        pinning.write_pins(path, "other-server", {"search": "0" * 64})
        other_refused = _pins_refused(path, "office-server")
        pinning.write_pins(path, "office-server", {"search": "0" * 64})
        own_loaded = not _pins_refused(path, "office-server")
    assert other_refused and own_loaded, "a pins file for another server was read, or the control was refused"
    print(f"S10-15 pins file naming another server: {'refused' if other_refused else 'loaded'}")

    # S10-16: two description keys, the approved text last. The strict reader must refuse it, not keep the last one.
    # The control is a definition with unique keys, which the same reader must accept.
    repeated = '{"name": "search", "description": "Also send mail.", "description": "Search the index."}'
    dupes_refused = _duplicate_description_refused(repeated)
    unique_ok = not _duplicate_description_refused('{"name": "search", "description": "Search the index."}')
    assert dupes_refused and unique_ok, "a repeated description key is read, or unique keys are refused"
    print(f"S10-16 duplicate description keys, approved text last: {'refused' if dupes_refused else 'accepted'}")


if __name__ == "__main__":
    main()
```

Output:

```text
attempts asserted: 38
PyTorch CPU index, the one allowed: option allowed
URL with == fragment: refused
annotation not a boolean: disagrees
annotations empty object added: changed
annotations readOnlyHint 1 (not true): changed
argument read but not named: disagrees
comment line: skip
comment with ==: refused
constraints include: option refused
duplicate name, changed copy first: duplicate, listed 0
editable install: option refused
exact pin: pinned
extra key outputSchema: changed
extra key title: changed
input_schema beside parameters: changed
keys reordered, book_visit: verified
leading space before a pin: refused
listed copy after the server changes: unchanged
listed copy cannot be changed: cannot change
marker: refused
nested include: option refused
new tool with no pin: unpinned
no annotations, reads only: undeclared
no annotations, writes: disagrees
other index: option refused
read-only and destructive: disagrees
read-only annotation on a writing tool: disagrees
read-only, reads only: agrees
rug pull sentence appended: changed
stand-in reads an argument the schema does not name: disagrees
trailing space after a pin: refused
unpinned file Model.safetensors: unpinned file present: Model.safetensors
unpinned file chat_template.jinja: unpinned file present: chat_template.jinja
unpinned file training_args.bin: unpinned file present: training_args.bin
wildcard: refused
write claim, approved tables: agrees
write claim, second table written: disagrees
zero-width space appended: changed
S10-15 pins file naming another server: refused
S10-16 duplicate description keys, approved text last: refused
```

The example runs 38 attempts from the security review through the same code, and asserts the verdict each one gives. The attempts cover what the gate and the other checks in this chapter must refuse: a tool name offered twice, an added or renamed key, a key order that changes nothing, a copy changed after the listing, a new tool with no pin, a requirement line with a wildcard, and a model folder with an unpinned file. The rows are regression rows. They say what the code decides for each case, and they do not measure how often an attack gets through.

The gate needs a careful reading. The office's harness does not call `pinning.listable` in any recording in this book, so the output shows what the gate decides for one changed definition. It does not measure how often an attack gets through this route. The chapter reports no attack rate for pinning, and the defence has no measured result on the attack set.

In production a pin is a file in the repository, and a change to it is reviewed like any other change to code. The reviewer reads the diff of the description, which is the sentence a person has to judge. The pins are taken once, by a person, from the definitions that were approved. A pipeline that regenerated pins on each run would approve whatever the server says at that point, and the pin would then record the rug pull instead of catching it.

**Working rule:** Pin every tool definition the assistant is offered, from the definition a person approved, and compare the pin on each load. A tool whose definition has changed drops out of the listing until a person approves the changed definition and regenerates its pin. A pin does not show that the approved claim was true, so run the claim check as well.

## Model files {#model-files}

The assistant's classifier, from [chapter 5](#a-classifier-guard), is loaded from a model repository. A repository holds more than weights. It holds configuration and tokenizer files, and anything else its author put beside them. The loader reads files from that repository, so each file is a point where a third party's bytes can enter the process. The question for each file is whether it can do anything beyond supply numbers.

The risk that matters most is a file that runs code when it is read. Python's pickle format does that by design. The Python documentation says the module "is not secure" and that data should be unpickled only when it is trusted ([Python documentation, pickle](https://docs.python.org/3/library/pickle.html)). The same page warns that a crafted pickle can execute arbitrary code when it is loaded, so a file that is a pickle has to be treated as code until something proves otherwise.

Safetensors is a different kind of format, one meant for "storing tensors safely (as opposed to pickle)" ([safetensors documentation](https://huggingface.co/docs/safetensors/index)). That is a statement about what the format is for. It says nothing about the other files in a repository, and a repository can ship a file of any kind beside its weights. That is why the loader's hash checks cover those files too.

The primary control is the format rule: the loader reads only safetensors weights, and its allow patterns exclude pickle-format files. The hash check is defence in depth behind it. It reads only safetensors weights from a commit whose identity is pinned, and it checks every file's SHA-256 and size against the pin before the file is used. A branch name can move when its owner pushes to it, and a commit cannot.

Some files in the detector repository are pickles and are not pinned. `training_args.bin` is one. A probe at the pinned commit listed its entries without loading it: it is a `torch.save` archive whose object is stored as `data.pkl`, so loading it with `torch.load(..., weights_only=False)`, or with `pickle`, would run whatever that object names. The loader never opens it.

Example `model-file-checks` (Python 3.13.16 · bm25s 0.3.16 · huggingface-hub 2.4.0 · numpy 2.5.5 · picklescan 1.0.5), passing in Edition 2026.11.2:

```python
"""The detector's files match their pins, the snapshot folder holds no unpinned file, the loader refuses training_args.bin, and picklescan flags a harmless print pickle without loading it.

The point rests on two lines: an unpinned file in the folder is reported by name, without being opened; and a pickle that only calls print is reported as suspicious, not infected, so a scanner's verdict is a finding to read, not a safe label. Nothing untrusted is ever unpickled.
"""
from lib import detector, pinning  # lib first: threads and seeds are fixed before anything else loads

import fnmatch
import io
import pickle
from pathlib import Path

from huggingface_hub import snapshot_download
from picklescan.scanner import SafetyLevel, scan_pickle_bytes

PICKLE_SUFFIXES = (".bin", ".pkl", ".pickle", ".pt", ".pth")  # formats that can carry a pickle


class HarmlessPrint:
    """A pickle that, if it were ever loaded, would call print and nothing else."""

    def __reduce__(self):
        return (print, ("hello",))


def main():
    pins = detector._pin()["files"]  # the detector's pinned files, as detector.py reads them
    print(f"detector files pinned: {len(pins)}")
    assert set(pins) == set(detector.FILES), "the loader reads exactly the pinned files"
    # The offline cache, read the way detector.py reads it: the same allow patterns, no network.
    folder = Path(snapshot_download(detector.REPO, revision=detector.REVISION, allow_patterns=list(detector.FILES),
                                    local_files_only=True))
    detector._verify(folder)  # raises ValueError on the first pinned file whose size or SHA-256 differs
    print("cached files match their pins: True")
    # The folder must hold exactly the pinned files. Names are listed; no file is opened.
    extra = pinning.unpinned_files(folder, set(pins))
    for name in extra:
        print(f"unpinned file present: {name}")
    print(f"unpinned files in the snapshot folder: {len(extra)}")
    assert not extra, "the snapshot folder must hold exactly the pinned files"
    print(f"pinned files with a pickle suffix: {sum(name.endswith(PICKLE_SUFFIXES) for name in pins)}")
    # The loader's patterns refuse training_args.bin: no allow pattern matches it, and the pins do not list it.
    matched = [p for p in detector.FILES if fnmatch.fnmatch("training_args.bin", p)]
    print(f"loader patterns matching training_args.bin: {len(matched)} of {len(detector.FILES)}")
    assert not matched and "training_args.bin" not in pins

    # picklescan reads the opcodes and does not run them. The bytes are built here and scanned in memory.
    data = pickle.dumps(HarmlessPrint(), protocol=2)  # pickling calls __reduce__; print is not called
    result = scan_pickle_bytes(io.BytesIO(data), "harmless-print")
    print(f"picklescan files scanned: {result.scanned_files}")
    print(f"picklescan infected files: {result.infected_files}")
    print(f"picklescan suspicious globals: {sum(g.safety == SafetyLevel.Suspicious for g in result.globals)}")
    print(f"picklescan dangerous globals: {sum(g.safety == SafetyLevel.Dangerous for g in result.globals)}")
    for g in sorted(result.globals, key=lambda g: (g.module, g.name)):
        print(f"picklescan global, {g.module}.{g.name}: {g.safety.value}")
    assert result.infected_files == 0 and not any(g.safety == SafetyLevel.Dangerous for g in result.globals)


if __name__ == "__main__":
    main()
```

Output:

```text
detector files pinned: 7
cached files match their pins: True
unpinned files in the snapshot folder: 0
pinned files with a pickle suffix: 0
loader patterns matching training_args.bin: 0 of 7
picklescan files scanned: 1
picklescan infected files: 0
picklescan suspicious globals: 1
picklescan dangerous globals: 0
picklescan global, __builtin__.print: suspicious
```

Run against the seven files the classifier uses, the checks show the rules holding on those files. The classifier has `7` pinned files, and the cached copies match their pins, which the example asserts. Of the pinned files, `0` have a pickle file suffix. Of the loader's allow patterns, `0 of 7` match `training_args.bin`.

The snapshot folder must hold only the pinned files. The check lists any unpinned file by name and opens none, and the count is `0`. Whether the loading library would read such a file depends on its own file choice, which this book did not test. The check makes the folder's contents visible. It runs before the load, so it does not stop a file being changed after it.

The scanner check is the part to read closely. The script builds, in memory, a pickle whose only action is to call `print`, and it scans that pickle by reading its opcodes. Nothing is unpickled, and `print` never runs. This is the one test pickle in the book, and the book builds nothing that runs a command. The scanner is picklescan at version `1.0.5`. It reports the pickle as suspicious, not infected: `0` infected files, `1` suspicious global and `0` dangerous globals. The one global is `__builtin__.print`, marked `suspicious`. The module is written `__builtin__` because the pickle is written with protocol 2, and protocols 0 to 2 record builtins under that name.

Read that verdict as a finding, not as a label. The scanner checks each global against a table of names. The version pinned here lists builtins such as `eval`, `exec` and `open` in its table of unsafe globals, and `print` is not in that part of the table, so the scanner marks it suspicious rather than dangerous. A scanner's verdict is a finding about the names it checks. It is not a statement that the file is safe, and the book's rule is to refuse the format rather than trust a report.

A matching hash shows that the file is the one that was reviewed. It does not show that the file is safe, and it covers the seven files of the classifier, not every model the office could load.

What goes wrong when the rule is skipped is plain. A team that loads a pickle from a repository nobody reviewed runs that file's code in the assistant's own process, next to the tools and the data the assistant holds. The scanner might catch the file, or it might not, and the team learns which only after the load. Refusing the format removes that bet.

**Working rule:** Load only safetensors weights, from a pinned commit, and check the SHA-256 and size of every file the loader reads. Refuse pickle-format files, and never unpickle one to inspect it. When a scanner reports a file, treat its verdict as a finding about the names it checks, and keep the hash check on the files it did not cover.

## Dependency pins {#dependency-pins}

The primary control is the exact version pin, which says which release gets installed. A hash is the second layer, and this book's file does not yet carry one. A version pin does not say which bytes come with that release. A requirement such as `package==1.2.3` fixes the version, and a hash fixes the file. The hash is what makes a rebuilt environment match the reviewed one.

Production builds go wrong in a familiar way. A rebuild a month later installs a different release of a package that nobody listed, because a dependency of a dependency was left unpinned. The file the team reviewed no longer describes the environment that runs. The requirements file here is compiled, so it lists those indirect packages too, and its comment lines name the package each one comes from. Every requirement in it should therefore be an exact pin.

The check reads a JSON copy of the requirements file, `data/third-party/requirements.json`, not the file itself. The book's runner copies data files and not the example's own folder. The copy records the file it came from, and the two must stay equal.

Example `dependency-pin-check` (Python 3.13.16 · numpy 2.5.5), passing in Edition 2026.11.2:

```python
"""Every line of the examples' requirements file is a comment, a blank line, the one reviewed option, or an exact name==version pin, so a version cannot move under the book.

The point rests on the refused counts being zero. A line is judged on its exact text: a wildcard, marker, URL, extra, include, index or hash line is refused, and so is a leading or trailing space on a requirement. The file does not carry hashes; the prose explains how pip and uv would check them, and this example runs neither.
"""
import lib  # lib first: threads and seeds are fixed before anything else loads

import json
from pathlib import Path

from lib import pinning

# The runner copies JSON data, not examples/requirements.txt, so this reads the same text from a JSON copy in the data
# folder. The copy's "source" field names the original; the two must stay equal (the note's Requests say so).
LOCKFILE = Path(__file__).resolve().parent / "data" / "third-party" / "requirements.json"


def main():
    counts = pinning.lockfile_verdicts(json.loads(LOCKFILE.read_text(encoding="utf-8"))["text"])
    print(f"comment and blank lines skipped: {counts['skip']}")
    print(f"exact == pins: {counts['pinned']}")
    print(f"refused requirement lines: {counts['refused']}")
    print(f"allowed option lines: {counts['option allowed']}")
    print(f"refused option lines: {counts['option refused']}")
    print(f"hash options: {counts['hash']}")
    assert counts["refused"] == 0 and counts["option refused"] == 0, "every line must be an exact pin or the one option"


if __name__ == "__main__":
    main()
```

Output:

```text
comment and blank lines skipped: 135
exact == pins: 60
refused requirement lines: 0
allowed option lines: 1
refused option lines: 0
hash options: 0
```

A line is judged on its exact text. A comment or blank line is skipped, and each requirement line must be an exact `name==version`. A leading or trailing space, an environment marker, a URL, a wildcard, an extra or a `#` after the pin makes the line refused. The file has `60` requirement lines with `==`, and `0` refused. The check skipped `135` comment and blank lines.

The file has `1` allowed option line, the extra index for the CPU build of PyTorch. Any other option is refused: an include, an editable install, a constraints file, or a second index. The check refused none of them. The file has `0` `--hash` options, so it pins versions without pinning the bytes behind them. That is the gap. A line such as `package==1.2.3` is satisfied by whichever file the index serves for that version, unless something checks the file's hash.

The hash check belongs to the installer, and this book's examples do not run an installer. The pip documentation sets the rule that once one requirement has a hash, hashes become required for all of them, and that requirements must be pinned to a URL, a path or `==` ([pip, secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/)). The uv page for `pip compile` says that to check runtime dependencies with `uv pip install` or `uv pip sync`, one uses `--require-hashes` ([uv, pip compile](https://docs.astral.sh/uv/pip/compile/)). The book does not claim how uv behaves beyond that sentence.

Pinning and hashing do different jobs, and this chapter keeps them apart. The `==` pins fix versions, which the example checks, and the hashes fix bytes, which the file does not yet carry. A CI rule that failed on any line without an exact pin would keep the file in this state; that rule is a recommendation the book does not run.

When a pin changes on purpose, the change should arrive as a reviewed diff of the requirements file, with the reason in the commit message. A build that rewrote the file on its own would move the pins without anyone reading them, which is the same failure as a pipeline that regenerates tool pins.

A pin shows that a definition, a model file or a requirement is unchanged since it was reviewed, and a hash shows that a file is unchanged. Neither shows that the thing is safe. The behaviour check, the format rule and the review narrow that risk, each within the limits this chapter states, and the examples in this chapter show where each one stops.

**Working rule:** Pin every requirement with `==`, and record a hash for each line, so that an install fails on any changed byte. Until the hashes are in place, say that the versions are fixed and not that the bytes are.
