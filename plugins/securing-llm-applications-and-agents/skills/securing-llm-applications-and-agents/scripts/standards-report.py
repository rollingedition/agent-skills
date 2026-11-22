"""Each defence the book measures, with its label and the confirmed risk IDs it addresses.

The point rests on `defences measured` and on the assert that the table covers exactly those defences: no defence is
reported without a label and a risk, and no row is left for a defence the book does not measure.
"""
from lib import gate, replay, variants  # lib first: threads and seeds are fixed here

LABELS = ("design", "harness", "input", "prompt")  # the four places a defence can sit in the system


def measured() -> list[str]:
    """The variant names that have a recording, with the undefended and control rows left out, in name order."""
    names = []
    for name in sorted(variants.VARIANTS):
        if name in gate.NOT_DEFENCES:
            continue
        if any((replay.RECORDED / f"{name}{suffix}").exists() for suffix in ("-dev", "")):  # dev or own recording
            names.append(name)
    return names


def main():
    names = measured()  # the detector included: its row is in lib/variants.py
    print(f"defences measured: {len(names)}")
    assert set(names) == set(gate.DEFENCE_STANDARDS), "the standards table and the measured defences differ"
    for name in names:
        label, risks = gate.DEFENCE_STANDARDS[name]
        assert label in LABELS, f"unknown label for {name}"
        print(f"{name}, label: {label}")
        print(f"{name}, risks: {'; '.join(risks)}")


if __name__ == "__main__":
    main()
