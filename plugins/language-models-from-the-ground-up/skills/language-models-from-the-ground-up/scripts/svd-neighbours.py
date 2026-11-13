from lib.vectors import DIMENSIONS, nearest, svd_vectors

vectors, vocabulary = svd_vectors()
index = {token: i for i, token in enumerate(vocabulary)}

print("dimensions per token:", DIMENSIONS)
for token in ["patio</w>", "outdoor</w>", "sofa</w>", "oak</w>", "blue</w>", "48</w>"]:
    neighbours = nearest(vectors, vocabulary, vectors[index[token]], k=4, skip=(token,))
    print(f"{token:<12} -> " + ", ".join(f"{t} {s:.2f}" for t, s in neighbours))
print("cosine(patio, outdoor):", f"{float(vectors[index['patio</w>']] @ vectors[index['outdoor</w>']]):.2f}")
