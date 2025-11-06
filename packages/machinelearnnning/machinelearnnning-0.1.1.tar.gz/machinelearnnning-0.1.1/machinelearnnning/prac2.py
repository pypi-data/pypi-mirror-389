def prac2():
    code = '''
    import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn import tree as sk_tree

data = {
    'Age': ['<=30', '<=30', '31-40', '>40', '>40', '>40', '31-40', '<=30', '<=30', '>40', '<=30', '31-40', '31-40', '>40'],
    'Income': ['High', 'High', 'High', 'Medium', 'Low', 'Low', 'Low', 'Medium', 'Low', 'Medium', 'Medium', 'Medium', 'High', 'Medium'],
    'Student': ['No', 'No', 'No', 'No', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'No'],
    'Credit Rating': ['Fair', 'Excellent', 'Fair', 'Fair', 'Fair', 'Excellent', 'Excellent', 'Fair', 'Fair', 'Fair', 'Excellent', 'Excellent', 'Fair', 'Excellent'],
    'Buys Computer': ['No', 'No', 'Yes', 'Yes', 'Yes', 'No', 'Yes', 'No', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'No']
}

df = pd.DataFrame(data)

df_encoded = df.apply(lambda x: pd.factorize(x)[0])
df_encoded.head()

classifier = sk_tree.DecisionTreeClassifier(criterion='entropy')
classifier = classifier.fit(df_encoded.iloc[:,:-1], df_encoded.iloc[:,-1])

feature_names = df.columns[:-1].tolist()
feature_names

class_name = df['Buys Computer'].unique().tolist()
class_name

plt.figure(figsize=(20,10))
sk_tree.plot_tree(classifier, feature_names=feature_names, class_names=class_name, filled=True)
plt.show()

test_sample = {
    'Age': '<=30',
    'Income': 'Medium',
    'Student': 'Yes',
    'Credit Rating': 'Fair'
}

test_df = pd.DataFrame([test_sample]).apply(lambda x: pd.factorize(df[x.name])[0][df[x.name].tolist().index(x[0])])

sklearn_pred = classifier.predict([test_df])
decoded_pred = pd.factorize(df['Buys Computer'])[1][sklearn_pred[0]]
print(f"Decision Tree Prediction: {decoded_pred}")
'''
    return code