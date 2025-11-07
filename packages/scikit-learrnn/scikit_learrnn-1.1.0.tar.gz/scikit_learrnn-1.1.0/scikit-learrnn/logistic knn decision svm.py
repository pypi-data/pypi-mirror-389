##Discriminative Models
#a. Logistic Regression – Perform binary classification using logistic regression. Calculate accuracy, precision, and recall, and understand the ROC curve.
CODE:
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,confusion_matrix
df=pd.read_csv('pima-indians-diabetes.csv',header=None)
print(df.head(),"\n")

X=df.iloc[:,:-1]
y=df.iloc[:,-1]
X_train,X_test,Y_train,Y_test=train_test_split(X,y,test_size=0.25,random_state=1)

log=LogisticRegression()
log.fit(X_train,Y_train)
lpred=log.predict(X_test)

print(confusion_matrix(Y_test,lpred),"\n")
print(accuracy_score(Y_test,lpred),"\n")


#B.) Implement and demonstrate the k-nearest Neighbour algorithm. Read the training data from a CSV file and build the model to classify a test sample. Print both correct and wrong predictions.
CODE:
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix

df=pd.read_csv('pima-indians-diabetes.csv',header=None)
print(df.head(2),"\n")
x=df.iloc[:,:-1]
print(x.head(2),"\n")
y=df.iloc[:,-1]
print(y.head(2),"\n")

xtrain,xtest,ytrain,ytest=train_test_split(x,y,test_size=0.25,random_state=1)
kclassifier=KNeighborsClassifier(n_neighbors=6)
kclassifier.fit(xtest,ytest)
kclassifier.fit(xtrain,ytrain)
kpred=kclassifier.predict(xtest)
print(accuracy_score(ytest,kpred),"\n")
print(confusion_matrix(ytest,kpred),"\n")



#C.) Build a decision tree classifier or regressor—control hyperparameters like tree depth to avoid overfitting. Visualise the tree.
CODE:
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score,confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt

data = load_iris()
X=data.data
y=data.target
xtrain,xtest,ytrain,ytest=train_test_split (X,y,test_size=0.25,random_state=1)
tree=DecisionTreeClassifier(max_depth=4)
tree.fit(xtrain,ytrain)
DecisionTreeClassifier(max_depth=4)
pred=tree.predict(xtest)
print(accuracy_score(ytest,pred),"\n")
print(confusion_matrix(ytest,pred),"\n")
plot_tree(tree)
plt.show()





#D.)  Implement a Support Vector Machine for any relevant dataset.
CODE:
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

data= load_breast_cancer()
X=data.data
y=data.target
xtrain,xtest,ytrain,ytest=train_test_split (X,y,test_size=0.25,random_state=1)

model1=SVC(kernel='linear')
model1.fit(xtrain,ytrain)
preds=model1.predict(xtest)

print(accuracy_score(ytest,preds),"\n")

model2=SVC(kernel='poly')
model2.fit(xtrain,ytrain)
preds2=model2.predict(xtest)

print(accuracy_score(ytest,preds2))
