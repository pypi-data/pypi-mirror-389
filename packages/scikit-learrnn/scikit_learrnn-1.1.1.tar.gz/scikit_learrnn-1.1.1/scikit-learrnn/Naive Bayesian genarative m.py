#A.) Implement and demonstrate the working of a Naive Bayesian classifier using a sample data set. Build the model to classify a test sample.
CODE:
from sklearn.datasets import load_breast_cancer
from  sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score , confusion_matrix

data = load_breast_cancer()
X=data.data
y=data.target
xtrain,xtest,ytrain,ytest=train_test_split (X,y,test_size=0.25,random_state=1)

gnb= GaussianNB()
gnb.fit(xtrain,ytrain)
GaussianNB()
preds=gnb.predict(xtest)
print(accuracy_score(ytest,preds))
print(confusion_matrix(ytest,preds))









