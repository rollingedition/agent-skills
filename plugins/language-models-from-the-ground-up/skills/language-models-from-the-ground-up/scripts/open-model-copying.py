from lib import open_model

copying = open_model.read("copying")
for label, probabilities in copying.items():
    for token, p in probabilities.items():
        print(f"SmolLM2-360M, {label}, P({token.strip()}):", f"{p:.2f}")
