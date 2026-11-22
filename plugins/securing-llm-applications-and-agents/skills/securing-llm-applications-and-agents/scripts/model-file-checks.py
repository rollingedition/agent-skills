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
