#Linear Models

#A.) Simple Linear Regression – Fit a linear regression model on a dataset. Interpret coefficients, make predictions, and evaluate performance using metrics like R-squared and MSE.
CODE:
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

df=pd.read_csv('SalaryData.csv')
print(df.head(3),"\n")

X=df.iloc[:,:-1]
print(X.shape,"\n")

y=df['Salary']
lr=LinearRegression()

xtrain,xtest,ytrain,ytest=train_test_split(X,y,test_size=0.25,random_state=1)
print(xtrain.shape,xtest.shape,ytrain.shape,ytest.shape,"\n")

lr.fit(xtrain,ytrain)
LinearRegression()
predictions=lr.predict(xtest)
print(mean_absolute_error(ytest,predictions),"\n")


#B.) Multiple Linear Regression – Extend linear regression to multiple features. Handle feature selection and potential multicollinearity.
CODE:
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

df=pd.read_csv('Advertising.csv')
print(df.head(2),"\n")

df.drop(['ID'],axis=1,inplace=True)
print(df.head(2),"\n")

X=df.iloc[:,:-1]
print(X.shape,"\n")

y=df.iloc[:,-1]
print(y.shape,"\n")

xtrain, xtest, ytrain, ytest = train_test_split(X, y, test_size=0.25, random_state=42)
print(xtrain.shape,xtest.shape,ytrain.shape,ytest.shape,"\n")

mlr=LinearRegression()
mlr.fit(xtrain,ytrain)
LinearRegression()
predictions=mlr.predict(xtest)

mae = mean_absolute_error(ytest, predictions)
mse = mean_squared_error(ytest, predictions)
r2 = r2_score(ytest, predictions)
print("Mean Absolute Error (MAE):", mae)
print("Mean Squared Error (MSE):", mse)
print("R-squared Score:", r2)

#C.) Regularised Linear Models (Ridge, Lasso) – Implement regression variants like LASSO and Ridge on any generated datasets.
CODE:
import pandas as pd
from sklearn.linear_model import Ridge,Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error,r2_score
df=pd.read_csv('Advertising.csv')
print(df.head(),"\n")

df.drop(['ID'],axis=1,inplace=True)
print(df.head(2),"\n")

X=df.iloc[:,:-1]
print(X.head(2),"\n")

y=df.iloc[:,-1]
print(y.head(2),"\n")

xtrain,xtest,ytrain,ytest=train_test_split(X,y,test_size=0.25,random_state=1)
rmodel=Ridge()
print(rmodel.get_params(),"\n")

rmodel.fit(xtrain,ytrain)
rpred=rmodel.predict(xtest)
print(mean_absolute_error(ytest,rpred),"\n")
print(r2_score(ytest,rpred),"\n")

lmodel=Lasso()
lmodel.fit(xtrain,ytrain)
lpred=lmodel.predict(xtest)
print(mean_absolute_error(ytest,lpred),"\n")
print(r2_score(ytest,lpred),"\n")
