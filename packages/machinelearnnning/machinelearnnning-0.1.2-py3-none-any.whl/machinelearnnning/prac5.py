def prac5():
    code = '''
    import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.datasets import load_wine
from sklearn.tree import DecisionTreeClassifier

from sklearn.ensemble import AdaBoostClassifier

data = load_wine()
X = pd.DataFrame(data.data, columns = data.feature_names)
y= pd.Series(data.target)

X_train, X_test, y_train, y_test = train_test_split(X,y, random_state=23, test_size=0.3)

dtclf = DecisionTreeClassifier(max_depth=1, criterion='gini', random_state=23)
dtclf.fit(X_train, y_train)

dtclf_pred = dtclf.predict(X_test)
dtclf_acc = round(accuracy_score(y_test, dtclf_pred),3)
print("Accuracy Score: ", dtclf_acc)

adaclf = AdaBoostClassifier(
    estimator=dtclf,
    n_estimators=50,
    learning_rate=0.5,
    random_state=23
)

adaclf.fit(X_train, y_train)

adaclf_pred = adaclf.predict(X_test)
adaclf_acc = round(accuracy_score(y_test, adaclf_pred),3)
print("Accuracy Score: ", adaclf_acc)

"""#Gradient Boosting"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.datasets import load_breast_cancer
from sklearn.tree import DecisionTreeClassifier

from sklearn.ensemble import GradientBoostingClassifier

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns = data.feature_names)
y= pd.Series(data.target)

X_train,X_test, y_train, y_test = train_test_split(X, y, random_state=42, test_size=0.3)

dtclf = DecisionTreeClassifier(random_state=42, criterion='gini')
dtclf.fit(X_train,y_train)

dtclf_pred = dtclf.predict(X_test)
dtclf_acc = round(accuracy_score(y_test, dtclf_pred),3)
print("Accuracy Score: ", dtclf_acc)

gb_model = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    random_state=42,
    max_depth=2
)
gb_model.fit(X_train, y_train)

gb_pred = gb_model.predict(X_test)
gb_acc = accuracy_score(y_test, gb_pred)
print("Accuracy Score: ", gb_acc)
'''
    return code