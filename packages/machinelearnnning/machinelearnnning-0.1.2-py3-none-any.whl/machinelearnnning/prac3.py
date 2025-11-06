def prac3():
    code = '''
    import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import tree
from sklearn.metrics import accuracy_score
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier

X,y = load_breast_cancer(return_X_y=True)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = DecisionTreeClassifier(random_state=0)
clf.fit(X_train, y_train)

y_train_predicted = clf.predict(X_train)
y_test_predicted = clf.predict(X_test)

accuracy_score(y_train, y_train_predicted)

accuracy_score(y_test, y_test_predicted)

plt.figure(figsize=(20,10))
tree.plot_tree(clf, filled=True)
plt.show()

path = clf.cost_complexity_pruning_path(X_train, y_train)
ccp_alphas, impurities = path.ccp_alphas, path.impurities
print("ccp_alphas: ", ccp_alphas)
print("Impurities:", impurities)

clfs = []

for ccp_alpha in ccp_alphas:
    clf = DecisionTreeClassifier(random_state=0, ccp_alpha=ccp_alpha)
    clf.fit(X_train, y_train)
    clfs.append(clf)

print("Last node in Decision Tree is {} with ccp_alpha: {}".format(clfs[-1].tree_.node_count, ccp_alphas[-1]))

train_scores = [clf.score(X_train, y_train) for clf in clfs]
test_scores = [clf.score(X_test, y_test) for clf in clfs]
fig, ax = plt.subplots()
ax.set_xlabel("alpha")
ax.set_ylabel("accuracy")
ax.set_title("Accuracy vs alpha for training and testing sets")
ax.plot(ccp_alphas[:-1], train_scores[:-1], marker='o', label="train", drawstyle="steps-post")
ax.plot(ccp_alphas[:-1], test_scores[:-1], marker='o', label="test", drawstyle="steps-post")
ax.legend()
plt.show()

clf = DecisionTreeClassifier(random_state=0, ccp_alpha=0.013)
clf.fit(X_train, y_train)

print(accuracy_score(y_train, clf.predict(X_train)))
print(accuracy_score(y_test, clf.predict(X_test)))

plt.figure(figsize=(20,10))
tree.plot_tree(clf, filled=True)
plt.show()

grid_parameters = {
    "criterion": ["gini","entropy"],
    "splitter": ["best","random"],
    "max_depth": range(2,50,1),
    "min_samples_split": range(1,15,1),
    "min_samples_leaf": range(1,15,1),
}

grid_search = GridSearchCV(estimator= clf, param_grid=grid_parameters, cv=5, n_jobs=-1)
grid_search.fit(X_train, y_train)

print(grid_search.best_params_)

clf = DecisionTreeClassifier(criterion="gini",ccp_alpha=0.013, min_samples_leaf=1, max_depth=7, min_samples_split=5, random_state=0, splitter='random')
clf.fit(X_train, y_train)

plt.figure(figsize=(20,10))
tree.plot_tree(clf, filled=True)
plt.show()

print(accuracy_score(y_train, clf.predict(X_train)))
print(accuracy_score(y_test, clf.predict(X_test)))
'''
    return code