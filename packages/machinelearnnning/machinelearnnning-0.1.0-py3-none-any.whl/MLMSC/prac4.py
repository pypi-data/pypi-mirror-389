def prac4():
    code = '''
    import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_curve, auc
from sklearn.preprocessing import label_binarize

iris = load_iris()
X = iris.data
y = iris.target

feature_names = iris.feature_names
class_names = iris.target_names
print(iris.target_names)

df = pd.DataFrame(X, columns=feature_names)
df['target'] = y
df['target_name'] = df['target'].map({i: name for i, name in enumerate(class_names)})
print(df.head(10))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

classifier = GaussianNB()
classifier.fit(X_train, y_train)

y_pred = classifier.predict(X_test)
y_proba = classifier.predict_proba(X_test)

accuracy = accuracy_score(y_test, y_pred)
matrix = confusion_matrix(y_test, y_pred)
report = classification_report(y_test, y_pred, target_names=class_names)

print(f"Accuracy: {accuracy}")
print("Confusion Matrix:")
print(matrix)
print("Classification Report:")
print(report)

plt.figure()
plt.imshow(matrix, interpolation='nearest', cmap = plt.cm.Blues)
plt.title('Confusion Matrix')
plt.colorbar()
tick_marks = np.arange(len(class_names))
plt.xticks(tick_marks, class_names, rotation=45)
plt.yticks(tick_marks, class_names)
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.tight_layout()
plt.show()

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(classifier, X_train, y_train, cv=cv, scoring='accuracy')
for i, score in enumerate(cv_scores, start=1):
    print(f"Fold {i}: {score:.3f}")
print(f"Mean Accuracy: {cv_scores.mean():.3f}")

y_test_bin = label_binarize(y_test, classes=[0,1,2])
n_classes = y_test_bin.shape[1]
fpr, tpr, roc_auc = {}, {}, {}

for i in range(n_classes):
  fpr[i], tpr[i], _ = roc_curve(y_test_bin[:,i], y_proba[:,i])
  roc_auc[i] = auc(fpr[i], tpr[i])

plt.figure()
for i in range(n_classes):
  plt.plot(fpr[i], tpr[i], label=f"ROC curve of class {class_names[i]} (area = {roc_auc[i]:.3f})")

plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) Curve')
plt.legend(loc="lower right")
plt.show()

new_samples = pd.DataFrame([
    {'sepal length (cm)': 5.1, 'sepal width (cm)': 3.5, 'petal length (cm)': 1.4, 'petal width (cm)': 0.2},
    {'sepal length (cm)': 6.2, 'sepal width (cm)': 3.4, 'petal length (cm)': 5.4, 'petal width (cm)': 1.5},
    {'sepal length (cm)': 5.9, 'sepal width (cm)': 3.0, 'petal length (cm)': 5.1, 'petal width (cm)': 2.1}
])

new_X = new_samples[feature_names].values
new_pred = classifier.predict(new_X)
new_proba = classifier.predict_proba(new_X)

for i in range(len(new_samples)):
  print(f"input: {list(new_samples.iloc[i])} -> predicted class: {class_names[new_pred[i]]}")
  print(f"predicted probabilities: {new_proba[i].max():.3f}")

print("\n hold-out accuracy score:", round(accuracy,3))
'''
    return code