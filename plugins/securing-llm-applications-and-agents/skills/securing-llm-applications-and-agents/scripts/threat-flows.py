"""Each attack location, and the one channel that delivers its text to the model: a tool that reads the carrier's field,
or the prompt's tool list. The injected text is checked in code and never printed. The probes are in lib/threat.py."""
from lib import cases, threat  # lib first: threads and seeds are fixed here


def main():
    # The counts are over the 120 fixed cases (dev and held-out). Chapter 1's 20 rough cases are left out.
    fixed = [c for c in cases.load_cases() if c.split != "rough"]
    rough = cases.load_cases("rough")
    print(f"fixed cases: {len(fixed)}")
    print(f"rough cases, chapter 1's set, not counted: {len(rough)}")
    flows = threat.location_channels()
    print(f"locations: {len(flows)}")
    for f in flows:
        loc = f["loc"]
        print(f"{loc}, fixed cases: {sum(1 for c in fixed if c.location == loc)}")
        print(f"{loc}, carrier kind: {f['kind']}")
        print(f"{loc}, state field changed: {f['field']}")
        print(f"{loc}, delivered by: {', '.join(f['channels']) or 'none'}")
        print(f"{loc}, read the field but do not carry it: {', '.join(f['quiet']) or 'none'}")


if __name__ == "__main__":
    main()
