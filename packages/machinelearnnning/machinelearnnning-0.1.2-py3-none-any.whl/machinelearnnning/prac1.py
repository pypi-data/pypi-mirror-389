def prac1():
    code = '''
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from mpl_toolkits.mplot3d import Axes3D
from sklearn.neighbors import KNeighborsClassifier

data = {
    'Age':[19,20,21,23,31,22,35,25,23,64,30,67,35,58,24],
    'Annual Income (k$)':[15,15,16,16,17,17,18,18,19,19,20,20,21,21,22],
    'Spending Score (1-100)':[39,81,6,77,40,76,6,94,3,72,79,65,76,76,94],
    'Segment':[0,1,0,1,0,1,0,1,0,1,1,1,1,1,1],
}

df = pd.DataFrame(data)
print(df.head())

X = df[['Age', 'Annual Income (k$)', 'Spending Score (1-100)']]
y = df['Segment']
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

knn = KNeighborsClassifier(n_neighbors=3, n_jobs=-1)
knn.fit(X_train, y_train)
y_pred = knn.predict(X_test)

print("\\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("\\nClassification Report:")
print(classification_report(y_test, y_pred))
print("\\nAccuracy Score:")
print(accuracy_score(y_test, y_pred))

plt.figure(figsize=(10, 6))
sns.scatterplot(x='Annual Income (k$)', y='Spending Score (1-100)', hue='Segment', data=df, palette='Set1')
plt.title('Customer Segments based on Annual Income and Spending Score')
plt.xlabel('Annual Income (k$)')
plt.ylabel('Spending Score (1-100)')
plt.show()

new_user_data = {'Age':[27], 'Annual Income (k$)':[23], 'Spending Score (1-100)':[60]}
new_user_df = pd.DataFrame(new_user_data)
new_user_scaled = scaler.transform(new_user_df)
new_user_segment = knn.predict(new_user_scaled)
new_user_df['Segment'] = new_user_segment
print("\\nNew User Data Prediction:")
print(new_user_df)

plt.figure(figsize=(10, 6))
sns.scatterplot(x='Annual Income (k$)', y='Spending Score (1-100)', hue='Segment', data=df, palette='Set1', marker='o')
sns.scatterplot(x='Annual Income (k$)', y='Spending Score (1-100)', hue='Segment', data=new_user_df, palette='Set2', marker='X', s=200)
plt.title('Customer Segments with New User Input')
plt.xlabel('Annual Income (k$)')
plt.ylabel('Spending Score (1-100)')
plt.legend()
plt.show()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X_scaled[:, 0], X_scaled[:, 1], X_scaled[:, 2], c=y, cmap='Set1', s=50, label='Existing Data')
ax.scatter(new_user_scaled[:, 0], new_user_scaled[:, 1], new_user_scaled[:, 2], c='green', marker='X', s=200, label='New User Data')

ax.set_xlabel('Age (scaled)')
ax.set_ylabel('Annual Income (scaled)')
ax.set_zlabel('Spending Score (scaled)')
plt.title('3D Plot of Customer Segments with New User Input')
ax.legend()
plt.show()
'''
    return code
