import numpy as np

from lib.queries import class_rows, train_classifier
from lib.store import load_labels, load_products, load_queries, product_text

products, queries, labels = load_products(), load_queries(), load_labels()
rows = class_rows(products)                     # one row per (product, class) for products with a class
vectorizer, model = train_classifier(products)  # the same, by scikit-learn's MultinomialNB
words = vectorizer.transform(product_text(rows))  # word counts: one row per (product, class), one column per word
classes = np.array(sorted(rows["label"].unique()))
print("product classes:", len(classes))
print("products without a class:", (products["product_class"] == "").sum())
print("products with several classes:", products["product_class"].str.contains("|", regex=False).sum())
missing = queries["query_class"].dropna()[lambda names: ~names.isin(classes)]
print("query classes that no product has:", len(missing))
print("query classes that no product has, names:", "; ".join(missing))

# Naive Bayes: log P(class) + sum over the query's words of log P(word | class), each word count smoothed by 1
word_counts = np.vstack([np.asarray(words[(rows["label"] == name).to_numpy()].sum(axis=0)) for name in classes])
log_prior = np.log(rows["label"].value_counts()[classes].to_numpy() / len(rows))
log_likelihood = np.log((word_counts + 1) / (word_counts.sum(axis=1, keepdims=True) + word_counts.shape[1]))
query_words = vectorizer.transform(queries["query"])
predicted = classes[np.asarray(query_words @ log_likelihood.T + log_prior).argmax(axis=1)]
print("same predictions as MultinomialNB:", (predicted == model.predict(query_words)).sum(), "of", len(queries))

queries = queries.assign(predicted=predicted)
print("predicted class equals query_class:", (queries["predicted"] == queries["query_class"]).sum())
exact = labels[labels["grade"] == 2].join(products["product_class"].str.split("|"), on="product_id")
for column, name in [("predicted", "predicted class"), ("query_class", "query_class")]:
    share = [exact.loc[exact["query_id"] == query_id, "product_class"].apply(lambda names: label in names).mean()
             for query_id, label in queries[column].items()]
    print(f"queries where most exact products have the {name}:", (np.array(share) > 0.5).sum())
for query_id in [133, 255, 410]:
    query, split, label = queries.loc[query_id, ["query", "split", "predicted"]]
    print(f"{query_id} ({split}): {query} -> {label}"
          f" (query_class: {queries.at[query_id, 'query_class']})")
print("predicted class for 7qt slow cooker:", queries.at[62, "predicted"])       # its query_class has no products
