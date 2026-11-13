"""Computes the store's model's loss on one product laid out as a request and a response, over every token and over
the response's tokens only. The prose's point rests on the last printed line, the average loss over the response only.
"""
import numpy as np

from lib import transformer
from lib.store import load_products

_, vocabulary, manifest = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
# the name is unique in the validation split, so its one row is the product
product = load_products("validation").query("name == 'double chaise patio furniture cover'").iloc[0]
# the text is cut at the model's longest length, so a long description may end early
ids = transformer.product_ids(product["name"], product["description"], index, manifest["settings"]["longest"])
sep = ids.index(index[transformer.SEP])           # the name plays the request; the description, the response

# the last position predicts nothing, since no token follows it, so its row is dropped
probabilities = transformer.softmax(transformer.forward(ids)[:-1])
# position i predicts the token at i + 1, so ids[1:] holds each position's target
# each token's loss, given the tokens before it
loss = -np.log(probabilities[np.arange(len(ids) - 1), ids[1:]])
response = np.arange(1, len(ids)) > sep                             # the description's tokens and its end
print("tokens predicted in the text:", len(loss))
print("tokens the instruction loss counts, the response's:", int(response.sum()))
print("average loss over every token:", f"{loss.mean():.3f}")
print("average loss over the response only:", f"{loss[response].mean():.3f}")
