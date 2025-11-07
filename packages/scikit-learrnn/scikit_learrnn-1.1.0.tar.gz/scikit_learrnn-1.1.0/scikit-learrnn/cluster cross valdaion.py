#A.) Implement cross-validation techniques (k-fold, stratified, etc.) for robust model evaluation.
CODE:
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score,KFold
import numpy as np
from sklearn.model_selection import StratifiedKFold

df=pd.read_csv('pima-indians-diabetes.csv')
print(df.head(2),"\n")
X=df.iloc[:,:-1]
y=df.iloc[:,-1]

tree=DecisionTreeClassifier()
KFold=KFold(n_splits=5)
score=cross_val_score(tree,X,y,cv=KFold)
print(score)
print(np.mean(score))

skf=StratifiedKFold(n_splits=5)
score2=cross_val_score(tree,X,y,cv=skf)
print(score2)
print(np.mean(score2))


#Clustering Models

#A.) Build a cluster model using GMM and compare with K-Means
CODE:
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt

dataset = pd.read_csv('gmm.csv')
print(dataset.head(10),"\n")

plt.figure()
plt.scatter(dataset['Weight'],dataset['Height'])
plt.xlabel('Weight')
plt.ylabel('Height')


Kmeans = KMeans(n_clusters=4)
Kmeans.fit(dataset)
KMeans(n_clusters=4)
predictions = Kmeans.predict(dataset)
dataframe1 = pd.DataFrame(dataset)
print(dataframe1,"\n")

dataframe1['predictions'] = predictions
print(dataframe1,"\n")



color=['red', 'yellow', 'green', 'blue']
for i in range(0,4):
    data=dataframe1[dataframe1['predictions']==i]
    plt.scatter(data['Weight'],data['Height'],c=color[i])
plt.show()

dataset_gmm = pd.read_csv('Clustering_gmm.csv')
gmm = GaussianMixture(n_components=4)
gmm.fit(dataset_gmm)
GaussianMixture(n_components=4)
pred = gmm.predict(dataset_gmm)
dataframe2 = pd.DataFrame(dataset_gmm)
dataframe2['predictions']=pred
color=['red', 'yellow','green','blue']
for i in range(0,4):
    data=dataframe2[dataframe2['predictions']==i]
    plt.scatter(data['Weight'],data['Height'],c=color[i])
