"""Loads the three doc versions and prints each one's section count, and how many section IDs all three share.

The shared IDs are the sections whose concept keeps one ID across versions (plan section 2.2)."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.docs import load_sections, versions

sections = load_sections()  # every version, sorted by version and section ID
all_versions = versions()  # the version labels present, sorted
for version in all_versions:
    print(f"sections in version {version}: {sum(1 for s in sections if s.version == version)}")

ids = {version: {s.section_id for s in sections if s.version == version} for version in all_versions}
shared = set.intersection(*ids.values())  # IDs present in every version
print(f"section IDs in all {len(all_versions)} versions: {len(shared)}")
print(f"section IDs in 2.0 but in neither 1.0 nor 1.1: {len(ids['2.0'] - ids['1.0'] - ids['1.1'])}")
