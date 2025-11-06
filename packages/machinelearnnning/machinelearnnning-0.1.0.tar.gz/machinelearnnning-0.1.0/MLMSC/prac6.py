def prac6():
    code = '''
import numpy as np
import pandas as pd
import scipy.cluster.hierarchy as sch
from sklearn.cluster import AgglomerativeClustering
import matplotlib.pyplot as plt

data=np.array([[1,2],[2,3],[3,4],[5,8],[6,9],[4.2,5.8]])

labels=['Plant A','Plant B','Plant C','Plant D','Plant E','Plant F']
methods=['single','complete','average']
dendograms={}
plt.figure(figsize=(20,15))
for i,method in enumerate(methods):

    linkage_matrix=sch.linkage(data,method=method)
    dendograms[method]=linkage_matrix


    plt.subplot(2,2,i+1)

    plt.title(f'Dendogram ({method.capitalize()} Linkage)')
    sch.dendrogram(linkage_matrix,labels=labels)
    plt.xlabel('Plants')
    plt.ylabel('Distance')
plt.tight_layout()
plt.show()

from inspect import currentframe
from mmap import MADV_MERGEABLE
def interpret_linkage_matrix(linkage_matrix,labels):
  print('Intermediate cluster')

  current_clusters={i:[labels[i]] for i in range(len(labels))}
  next_clusters_index=len(labels)
  for merge_idx, merge in enumerate(linkage_matrix):
    c1,c2,dist,_= merge
    c1,c2=int(c1),int(c2)

    new_cluster=current_clusters[c1]+current_clusters[c2]

    print(f"Step {merge_idx + 1}: Merge {current_clusters[c1]} and {current_clusters[c2]} at distance {dist:.2f}")

    current_clusters[next_clusters_index]=new_cluster
    del current_clusters[c1]
    del current_clusters[c2]

    next_clusters_index+=1

def interpret_linkage_matrix(linkage_Matrix,labels):
  print("\nIntermediate Cluster Results:")


  current_clusters={i:[labels[i]] for i in range(len(labels))}


  next_cluster_index=len(labels)

  for merge_idx, merge in enumerate(linkage_matrix):
    c1, c2, dist, _= merge

    c1, c2 = int(c1), int(c2)


    new_cluster = current_clusters[c1] + current_clusters[c2]


    print(f"Step {merge_idx + 1}: Merge {current_clusters[c1]} and {current_clusters[c2]} -> {new_cluster} (Distance:{dist:.2f})")


    current_clusters[next_cluster_index]=new_cluster


    del current_clusters[c1]
    del current_clusters[c2]

    next_cluster_index += 1



for method in methods:
  print(f"\n==={method.capitalize()} Linkage===")
  interpret_linkage_matrix(dendograms[method],labels)


def plot_clusters_with_labels(data, cluster_labels,title,labels):
  unique_labels=np.unique(cluster_labels)
  cmap=plt.cm.viridis
  colors = [cmap(i/max(unique_labels))for i in unique_labels]


  for i, color in zip(unique_labels, colors):

    cluster_points=data[cluster_labels==i]

    plt.scatter(cluster_points[:, 0], cluster_points[:, 1], c=[color], label=f"Cluster {i+1}", s=100)


  for idx in range(len(data)):
    plt.text(data[idx, 0] + 0.1, data[idx, 1], labels[idx], fontsize=9, color='black', ha='left', va='center')

  plt.title(title)

  plt.xlabel("Feature 1")
  plt.ylabel("Feature 2")
  plt.legend(loc='upper left')
  plt.show()

for method in methods:
  clustering = AgglomerativeClustering(n_clusters=2, linkage=method, metric='euclidean')
  cluster_labels = clustering.fit_predict(data)


  plot_clusters_with_labels(data, cluster_labels, f"Clusters ({method.capitalize()} Linkage with labels)", labels) # Fix: Added the 'labels' argument
  '''
    return code