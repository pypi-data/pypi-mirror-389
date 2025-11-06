def prac7():
    code = '''
    import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from seaborn import load_dataset

data = load_dataset('iris')
data.head()

data = data[['sepal_length', 'sepal_width']]
data.head()

scaler = StandardScaler()
scaled_data = scaler.fit_transform(data)

eps = .3
min_samples = 3
dbscan = DBSCAN(eps=eps, min_samples=min_samples)
labels = dbscan.fit_predict(scaled_data)

core_samples_mask = np.zeros_like(labels, dtype=bool)
core_samples_mask[dbscan.core_sample_indices_] = True

df = pd.DataFrame(data, columns=['sepal_length', 'sepal_width'])
df['cluster'] = labels
df["Type"] = ["Core" if core_samples_mask[i] else "Border" if labels[i] != -1 else "Noise" for i in range(len(labels))]

plt.figure(figsize=(8,6))
unique_labels = np.unique(labels)

for label in unique_labels:
  cluster_points = df[df["cluster"] == label]
  if label == -1:
      color = 'black'
  else:
    color = plt.cm.Set1(label / len(unique_labels))
  plt.scatter(cluster_points['sepal_length'], cluster_points['sepal_width'], color=color, label=f'Cluster {label}' if label != -1 else 'Noise',s=100)

for i, row in df.iterrows():
  label = f"{row['Type']}"
  plt.text(row["sepal_length"] + 0.2, row["sepal_width"] + 0.2, label, fontsize=8)

print('DBSCAN Results')
print(df)
'''
    return code