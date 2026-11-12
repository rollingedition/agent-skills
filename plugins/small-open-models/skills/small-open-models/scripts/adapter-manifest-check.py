"""Check an adapter's manifest and files before the route loads it, and show what happens to two edited copies.
check_adapter hashes manifest.json, each output file the manifest lists, and the three LoRA settings. make_app runs
the same check before it loads a model."""
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import tempfile  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
manifest, s_ok, s_n, f_ok, f_n, pinned = router_lib.check_adapter(RECORDED)
base = router_lib.pinned_revision(manifest["model"]) == manifest["model_version"]
print(f"adapter: {manifest['adapter']}")
print(f"base revision matches pin: {'yes' if base else 'no'}")
print(f"manifest matches pin: {'yes' if pinned else 'no'}")
print(f"settings matching: {s_ok}/{s_n}")
print(f"files matching: {f_ok}/{f_n}")
print("route may load: " + ("yes" if base and pinned and s_ok == s_n and f_ok == f_n else "no"))
with tempfile.TemporaryDirectory() as tmp:
    threshold = router_lib.edited_copy(RECORDED, Path(tmp) / "threshold", "manifest.json", "handoff_threshold", 0.0)
    extra = router_lib.edited_copy(RECORDED, Path(tmp) / "extra", "adapter/adapter_config.json", "future_key", 1)
    for label, folder in [("threshold copy", threshold), ("extra-key copy", extra)]:
        _, s_ok, s_n, f_ok, f_n, pinned = router_lib.check_adapter(folder)
        print(f"{label}: manifest matches pin {'yes' if pinned else 'no'}, settings {s_ok}/{s_n}, files {f_ok}/{f_n}")
        print(f"{label} refused by make_app: {'yes' if router_lib.refused_by_make_app(folder) else 'no'}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        router_lib.load_classifier(extra / "adapter")
    named = [w for w in caught if "future_key" in str(w.message)]  # only the warning about the extra key
    print(f"warnings naming the extra key while PEFT loads the copy: {len(named)}")
    print(f"that warning: {named[0].category.__name__}: {str(named[0].message).split('. ')[0]}.")
