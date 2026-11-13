from lib import transformer
from lib.store import load_products

_, vocabulary, manifest = transformer.load()
index = {t: i for i, t in enumerate(vocabulary)}
product = load_products("validation").query("name == 'double chaise patio furniture cover'").iloc[0]
cover, other = index["cover</w>"], index["set</w>"]

for name, label in [("double chaise patio furniture cover", "name as sold"),
                    ("double chaise patio furniture", "name without cover"),
                    ("double chaise patio furniture set", "name ending in set")]:
    ids = transformer.product_ids(name, product["description"], index, manifest["settings"]["longest"])
    sep = ids.index(index[transformer.SEP])
    furniture = [i for i in range(sep + 1, len(ids)) if ids[i] == index["furniture</w>"]]
    p = transformer.softmax(transformer.forward(ids)[furniture[1]])   # at the description's second `furniture`
    print(f"{label}, P(cover): {p[cover]:.2f}")
    print(f"{label}, P(set): {p[other]:.2f}")

phrase = "this outdoor patio furniture "
after = [d.split(phrase, 1)[1].split()[0] for d in load_products("train")["description"]
         if isinstance(d, str) and phrase in d and d.split(phrase, 1)[1].split()]
print("training descriptions with 'this outdoor patio furniture':", len(after))
print("followed by cover:", after.count("cover"))
