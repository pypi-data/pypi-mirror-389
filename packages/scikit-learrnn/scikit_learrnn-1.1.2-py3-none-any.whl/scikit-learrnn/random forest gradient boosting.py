#Ensemble Learning
#A.) Train a random forest ensemble. Experiment with the number of trees and feature sampling. Compare performance to a single decision tree.
CODE:
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

data = load_wine()
X=data.data
y=data.target
xtrain,xtest,ytrain,ytest=train_test_split (X,y,test_size=0.25,random_state=1)
print(X,"\n")
print(y,"\n")

tree=DecisionTreeClassifier()
forest=RandomForestClassifier()
tree.fit(xtrain,ytrain)
forest.fit(xtrain,ytrain)

tpred=tree.predict(xtest)
fpred=forest.predict(xtest)
taccuracy=accuracy_score(ytest,tpred)
faccuracy=accuracy_score(ytest,fpred)

if taccuracy<faccuracy:
    print("Random forest has better accuracy ", faccuracy)
else:
    print("Decision tree has better accuracy", taccuracy)



#B.) Implement a gradient boosting machine (e.g., XGBoost). Tune hyperparameters and explore feature importance.
CODE:
from sklearn.datasets import load_wine
from  sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

data = load_wine()
X=data.data
y=data.target
xtrain,xtest,ytrain,ytest=train_test_split (X,y,test_size=0.25,random_state=1)

ada=AdaBoostClassifier(estimator=LogisticRegression(),n_estimators=50)
ada.fit(xtrain,ytrain)
preds=ada.predict(xtest)
print(accuracy_score(ytest,preds))

gb=GradientBoostingClassifier(n_estimators=50)
gb.fit(xtrain,ytrain)
GradientBoostingClassifier(n_estimators=50)
preds2=gb.predict(xtest)
print(accuracy_score(ytest,preds2))
