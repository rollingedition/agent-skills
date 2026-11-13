import numpy as np

from lib import transformer
from lib.store import load_products

_, vocabulary, manifest = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
product = load_products("validation").query("name == 'double chaise patio furniture cover'").iloc[0]
ids = transformer.product_ids(product["name"], product["description"], index, manifest["settings"]["longest"])
sep = ids.index(index[transformer.SEP])           # the name plays the request; the description, the response

probabilities = transformer.softmax(transformer.forward(ids)[:-1])
loss = -np.log(probabilities[np.arange(len(ids) - 1), ids[1:]])     # each token's loss, given the tokens before it
response = np.arange(1, len(ids)) > sep                             # the description's tokens and its end
print("tokens predicted in the text:", len(loss))
print("tokens the instruction loss counts, the response's:", int(response.sum()))
print("average loss over every token:", f"{loss.mean():.3f}")
print("average loss over the response only:", f"{loss[response].mean():.3f}")
