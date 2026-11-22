"""Prints one block per office tool: what it reads and writes, whether its output carries outside text, whether its
definition is third-party, whether it reaches outside the office and whether it returns private records. The prose's
table rests on the 'untrusted output' and 'reaches outside' lines; their derivations are in lib/threat.py."""
from lib import cases, harness, threat, tools  # lib first: threads and seeds are fixed here


def main():
    rows = threat.table()
    print(f"tools in SPECS: {len(tools.SPECS)}")
    print(f"tools in the prompt list: {len(tools.TOOLS)}")
    # The prompt list and the code's table must name the same tools.
    assert {t["function"]["name"] for t in tools.TOOLS} == set(tools.SPECS)
    for name in sorted(rows):
        r = rows[name]
        print(f"{name}, reads: {', '.join(r['reads']) or 'none'}")
        print(f"{name}, writes: {', '.join(r['writes']) or 'none'}")
        print(f"{name}, untrusted output: {'yes' if r['untrusted_output'] else 'no'}")
        print(f"{name}, third-party definition (THIRD_PARTY_TOOLS): {'yes' if r['third_party_definition'] else 'no'}")
        print(f"{name}, reaches outside the office: {'yes, via ' + r['outward'] if r['outward'] else 'no'}")
        print(f"{name}, private records: {'yes' if r['private'] else 'no'}")
    # The prompt is a second channel: it holds the office's private values on every episode, whichever tools it offers.
    world = cases.load_world()
    hidden = threat.office()["hidden_context"]
    prompt = threat.system_prompt()
    print(f"system prompt holds the portal key: {'yes' if world.portal_key in prompt else 'no'}")
    print(f"system prompt holds the office's hidden context: {'yes' if hidden in prompt else 'no'}")
    untrusted_definitions = threat.marked_untrusted_definitions()
    print(f"tool definitions the prompt marks untrusted: {', '.join(untrusted_definitions) or 'none'}")
    # Checks behind the claims: the private tool is the one that reads tenant records, the prompt holds the key.
    assert [n for n, r in sorted(rows.items()) if r["private"]] == ["lookup_tenant"]
    assert world.portal_key in prompt and hidden in prompt
    assert untrusted_definitions == sorted(tools.THIRD_PARTY_TOOLS)


if __name__ == "__main__":
    main()
