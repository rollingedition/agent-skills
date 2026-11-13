from lib import open_model

for prefix, recorded in open_model.read("prefixes").items():
    shown = ", ".join(f"{token!r} {p:.2f}" for token, p in recorded["top"][:3])
    print(f"{prefix:<12} -> {shown}")
print("P(stool | outdoor bar), SmolLM2-360M:", f"{open_model.read('prefixes')['outdoor bar']['P( stool)']:.4f}")
